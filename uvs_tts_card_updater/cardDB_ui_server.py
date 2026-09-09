from __future__ import annotations

import json
import os
import re
import threading
import time
import traceback
import uuid
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import urllib3

import cardDB_generator as gen


APP_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = APP_DIR.parent
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
DEFAULT_JSON = WORKSPACE_DIR / "cardDB_fresh.json"
DEFAULT_LUA = WORKSPACE_DIR / "cardDB_fresh.lua"
DEFAULT_COLLISIONS = APP_DIR / "cardDB_ui_decisions.json"
DEFAULT_HISTORY = APP_DIR / "history.json"
DEFAULT_TTS_LUA = WORKSPACE_DIR / ".tts" / "bundled" / "card_db.664c59.lua"
DEFAULT_TTS_SAVE = (
    Path.home()
    / "OneDrive"
    / "Documents"
    / "My Games"
    / "Tabletop Simulator"
    / "Saves"
    / "TS_Save_20.json"
)
TTS_SAVES_DIR = DEFAULT_TTS_SAVE.parent
JOBS: dict[str, dict[str, Any]] = {}
JOBS_LOCK = threading.Lock()
HISTORY_LOCK = threading.Lock()

RE_VARIANT_SUFFIX = re.compile(r"\s+\[uvs_id\s+\d+\](?:\s+\d+)?$", re.I)
RE_EXTENSION_HINT = re.compile(
    r"images/extensions/([^/]+)/.*?extension_pdf\.php\?id=(\d+)",
    re.I | re.S,
)


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def resolve_path(value: str | None, default: Path) -> Path:
    if not value:
        return default
    path = Path(value)
    if not path.is_absolute():
        path = WORKSPACE_DIR / path
    return path.resolve()


def base_key_for(key: str) -> str:
    return RE_VARIANT_SUFFIX.sub("", gen.normalize_name(key))


def card_id(row: dict[str, Any]) -> str:
    return str(row.get("uvs_id") or row.get("image") or uuid.uuid4())


def make_preview_key(prefix: str, row: dict[str, Any], key: str | None = None) -> str:
    return f"{prefix}:{key or card_id(row)}"


def job_log(job: dict[str, Any], message: str) -> None:
    line = f"[{now()}] {message}"
    job["log"].append(line)
    print(line, flush=True)


def load_history() -> list[dict[str, Any]]:
    if not DEFAULT_HISTORY.exists():
        return []
    with DEFAULT_HISTORY.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        return []
    return [entry for entry in data if isinstance(entry, dict)]


def save_history(entries: list[dict[str, Any]]) -> None:
    DEFAULT_HISTORY.parent.mkdir(parents=True, exist_ok=True)
    with DEFAULT_HISTORY.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(entries[:250], handle, ensure_ascii=False, indent=2, sort_keys=True)


def add_history_entry(entry: dict[str, Any]) -> dict[str, Any]:
    full_entry = {
        "id": uuid.uuid4().hex,
        "timestamp": now(),
        **entry,
    }
    with HISTORY_LOCK:
        entries = load_history()
        entries.insert(0, full_entry)
        save_history(entries)
    return full_entry


def summarize_history_entry(entry: dict[str, Any]) -> dict[str, Any]:
    result = entry.get("result") or {}
    settings = entry.get("settings") or {}
    target = (
        result.get("target_tts_save")
        or result.get("target_tts_lua")
        or result.get("target_json")
        or settings.get("target_json")
        or ""
    )
    return {
        "id": entry.get("id", ""),
        "timestamp": entry.get("timestamp", ""),
        "type": entry.get("type", ""),
        "label": entry.get("label", ""),
        "extension_code": settings.get("extension_code", ""),
        "format": settings.get("format", ""),
        "target": target,
        "cards_total": result.get("cards_total", ""),
        "added": result.get("added", ""),
        "replaced_conflicts": result.get("replaced_conflicts", ""),
        "conflict_count": (entry.get("analysis") or {}).get("conflict_count", ""),
    }


def get_history_entry(entry_id: str) -> dict[str, Any] | None:
    for entry in load_history():
        if entry.get("id") == entry_id:
            return entry
    return None


def load_json_db(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return {str(k): dict(v) for k, v in data.items() if isinstance(v, dict)}


def grouped_existing(db: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for key, row in db.items():
        groups.setdefault(base_key_for(key), []).append(
            {
                "ref": make_preview_key("existing", row, key),
                "source": "existing",
                "key": key,
                "base_key": base_key_for(key),
                "name": key,
                "row": row,
                "image": row.get("image", ""),
                "uvs_id": row.get("uvs_id"),
                "type": row.get("type", ""),
            }
        )
    return groups


def incoming_entry(name: str, row: dict[str, Any]) -> dict[str, Any]:
    key = gen.normalize_name(name)
    return {
        "ref": make_preview_key("incoming", row),
        "source": "incoming",
        "key": key,
        "base_key": key,
        "name": name,
        "row": row,
        "image": row.get("image", ""),
        "uvs_id": row.get("uvs_id"),
        "type": row.get("type", ""),
    }


def compact_card(entry: dict[str, Any]) -> dict[str, Any]:
    row = entry["row"]
    return {
        "ref": entry["ref"],
        "source": entry["source"],
        "key": entry["key"],
        "base_key": entry["base_key"],
        "name": entry["name"],
        "image": entry.get("image", ""),
        "uvs_id": entry.get("uvs_id"),
        "type": entry.get("type", ""),
        "speed": row.get("speed"),
        "damage": row.get("damage"),
        "zone": row.get("zone"),
        "vitality": row.get("vitality"),
    }


def resolve_extension_id(
    session: Any,
    search_format: str,
    extension_code: str,
    max_pages: int,
    job: dict[str, Any],
) -> str | None:
    if extension_code.isdigit():
        return extension_code

    pages_to_check = min(max_pages, 25)
    needle = extension_code.lower()
    for page in range(pages_to_check):
        html = gen.fetch_listing(session, search_format, page)
        for code, extension_id in RE_EXTENSION_HINT.findall(html):
            if code.lower() == needle:
                job_log(job, f"Resolved set {extension_code} to UVS Ultra extension id {extension_id}")
                return extension_id
        if needle in html.lower():
            id_match = re.search(r"extension_pdf\.php\?id=(\d+)", html, re.I)
            if id_match:
                extension_id = id_match.group(1)
                job_log(job, f"Resolved set {extension_code} to UVS Ultra extension id {extension_id}")
                return extension_id
        job_log(job, f"Resolver checked listing page {page + 1}")
    return None


def scrape_cards(settings: dict[str, Any], job: dict[str, Any]) -> list[dict[str, Any]]:
    search_format = settings.get("format") or "legacy"
    set_filter = (settings.get("extension_code") or settings.get("extension_id") or "").strip().lower()
    extension_code = "" if set_filter.isdigit() else set_filter
    max_pages = int(settings.get("max_pages") or 300)
    stop_empty_pages = int(settings.get("stop_empty_pages") or 2)
    sleep_listing = float(settings.get("sleep_listing") or 0.15)
    sleep_showcard = float(settings.get("sleep_showcard") or 0.03)
    insecure = bool(settings.get("insecure"))

    if not set_filter:
        raise ValueError("UVS Ultra extension number is required")

    job_log(job, f"Starting scrape for extension={set_filter} format={search_format}")
    session = gen.make_session()
    if insecure:
        session.verify = False
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        job_log(job, "TLS certificate verification disabled")

    extension_id = resolve_extension_id(session, search_format, set_filter, max_pages, job)
    if extension_id:
        job_log(job, f"Using source set filter extension[]={extension_id}")
    else:
        job_log(job, "Could not resolve numeric extension id; falling back to image URL filtering")

    showcards: dict[int, str] = {}
    empty_pages = 0
    for page in range(max_pages):
        html = gen.fetch_listing(session, search_format, page, extension_id)
        found = gen.extract_showcards(html)
        job_log(job, f"Listing page {page + 1}: {len(found)} showcards")
        if not found:
            empty_pages += 1
            if empty_pages >= stop_empty_pages:
                job_log(job, f"Stopping after {empty_pages} empty pages")
                break
        else:
            empty_pages = 0
            showcards.update(found)
        time.sleep(sleep_listing)

    if not showcards:
        raise RuntimeError("No showcards found for the selected format")

    cards: list[dict[str, Any]] = []
    total = len(showcards)
    for idx, (cid, rel) in enumerate(sorted(showcards.items()), start=1):
        html = gen.fetch_showcard(session, rel)
        parsed = gen.parse_showcard(html, cid, search_format)
        row = parsed["data"]
        if extension_id and not extension_code:
            cards.append(incoming_entry(parsed["name"], row))
        elif gen.row_matches_extension(row, extension_code):
            cards.append(incoming_entry(parsed["name"], row))
        if idx % 100 == 0 or idx == total:
            job_log(job, f"Parsed {idx}/{total}; matched {len(cards)}")
        time.sleep(sleep_showcard)

    job_log(job, f"Matched {len(cards)} cards for extension {set_filter}")
    return cards


def analyze_cards(settings: dict[str, Any], incoming: list[dict[str, Any]]) -> dict[str, Any]:
    target_json = resolve_path(settings.get("target_json"), DEFAULT_JSON)
    existing = load_json_db(target_json)
    existing_groups = grouped_existing(existing)

    incoming_groups: dict[str, list[dict[str, Any]]] = {}
    for entry in incoming:
        incoming_groups.setdefault(entry["base_key"], []).append(entry)

    conflicts: list[dict[str, Any]] = []
    new_cards: list[dict[str, Any]] = []
    skipped_same_image = 0

    for base_key, entries in sorted(incoming_groups.items()):
        existing_entries = existing_groups.get(base_key, [])
        existing_images = {str(e.get("image") or "") for e in existing_entries}
        incoming_images = {str(e.get("image") or "") for e in entries}
        new_images = incoming_images - existing_images
        has_same_name_different_image = bool(existing_entries and new_images)
        has_incoming_variants = len(incoming_images) > 1

        if has_same_name_different_image or has_incoming_variants:
            conflicts.append(
                {
                    "base_key": base_key,
                    "choices": [compact_card(e) for e in existing_entries + entries],
                    "default_ref": (existing_entries + entries)[0]["ref"],
                }
            )
            continue

        if not existing_entries:
            new_cards.extend(compact_card(e) for e in entries)
        else:
            skipped_same_image += len(entries)

    return {
        "target_json": str(target_json),
        "target_lua": str(resolve_path(settings.get("target_lua"), DEFAULT_LUA)),
        "existing_count": len(existing),
        "incoming_count": len(incoming),
        "new_count": len(new_cards),
        "conflict_count": len(conflicts),
        "skipped_same_image": skipped_same_image,
        "new_cards": new_cards,
        "conflicts": conflicts,
        "incoming_full": incoming,
    }


def backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_name(f"{path.name}.bak_{stamp}")
    backup_path.write_bytes(path.read_bytes())
    return backup_path


def lua_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return f'"{gen.lua_escape(str(value))}"'


def build_image_lines(carddb: dict[str, dict[str, Any]]) -> str:
    lines = []
    for key in sorted(carddb.keys()):
        image = carddb[key].get("image")
        if image:
            lines.append(f'cardDbImages["{gen.lua_escape(key)}"] = "{gen.lua_escape(str(image))}"')
    return "\n".join(lines)


def build_meta_lines(carddb: dict[str, dict[str, Any]]) -> str:
    lines = ["local cardDbMeta = {"]
    field_order = ["standard", "legacy", "uvs_id", "speed", "damage", "zone", "type", "vitality", "image"]
    for key in sorted(carddb.keys()):
        row = carddb[key]
        fields = []
        for field in field_order:
            if field in row:
                fields.append(f"{field}={lua_value(row[field])}")
        for field in sorted(k for k in row.keys() if k not in field_order):
            fields.append(f"{field}={lua_value(row[field])}")
        lines.append(f'  ["{gen.lua_escape(key)}"] = {{ {", ".join(fields)} }},')
    lines.append("}")
    return "\n".join(lines)


def list_tts_saves() -> list[dict[str, Any]]:
    if not TTS_SAVES_DIR.exists():
        return []
    saves = []
    for path in TTS_SAVES_DIR.glob("TS_Save_*.json"):
        stat = path.stat()
        save_name = ""
        try:
            with path.open("r", encoding="utf-8-sig") as handle:
                data = json.load(handle)
            save_name = str(data.get("SaveName") or "")
        except Exception:
            save_name = ""
        saves.append(
            {
                "path": str(path),
                "file": path.name,
                "save_name": save_name,
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "size": stat.st_size,
            }
        )
    saves.sort(key=lambda item: item["modified"], reverse=True)
    return saves


def replace_between(text: str, start_marker: str, end_marker: str, replacement: str) -> str:
    start = text.find(start_marker)
    if start < 0:
        raise ValueError(f"Could not find marker: {start_marker}")
    content_start = start + len(start_marker)
    end = text.find(end_marker, content_start)
    if end < 0:
        raise ValueError(f"Could not find marker after {start_marker}: {end_marker}")
    return text[:content_start] + "\n" + replacement + "\n" + text[end:]


def rebuild_carddb_lua_text(text: str, carddb: dict[str, dict[str, Any]]) -> str:
    image_lines = build_image_lines(carddb)
    meta_block = build_meta_lines(carddb)
    text = replace_between(
        text,
        "local cardDbImages = {}\n",
        "\n-- Card metadata table generated",
        image_lines,
    )
    text = replace_between(
        text,
        "local cardDbMeta = {\n",
        "\n}\n\n-- Resolve normalized key used across image/meta/errata lookups.",
        meta_block[len("local cardDbMeta = {\n") :],
    )
    return text


def publish_to_tts(payload: dict[str, Any]) -> dict[str, Any]:
    source_json = resolve_path(payload.get("source_json"), DEFAULT_JSON)
    target_lua = resolve_path(payload.get("target_tts_lua"), DEFAULT_TTS_LUA)
    carddb = load_json_db(source_json)
    if not carddb:
        raise ValueError(f"No cards found in {source_json}")
    if not target_lua.exists():
        raise FileNotFoundError(f"TTS card DB Lua not found: {target_lua}")

    text = target_lua.read_text(encoding="utf-8")
    text = rebuild_carddb_lua_text(text, carddb)
    target_lua.parent.mkdir(parents=True, exist_ok=True)
    backup_path = backup(target_lua)
    target_lua.write_text(text, encoding="utf-8", newline="\n")
    result = {
        "source_json": str(source_json),
        "target_tts_lua": str(target_lua),
        "backup": str(backup_path) if backup_path else "",
        "cards_total": len(carddb),
        "image_rows": sum(1 for row in carddb.values() if row.get("image")),
    }
    add_history_entry(
        {
            "type": "publish_tts_lua",
            "label": target_lua.name,
            "settings": {
                "source_json": str(source_json),
                "target_tts_lua": str(target_lua),
            },
            "result": result,
        }
    )
    return result


def iter_tts_objects(root: Any) -> Any:
    if isinstance(root, dict):
        yield root
        for key in ("ObjectStates", "ContainedObjects"):
            for child in root.get(key, []) or []:
                yield from iter_tts_objects(child)
    elif isinstance(root, list):
        for item in root:
            yield from iter_tts_objects(item)


def find_card_db_save_object(save_data: dict[str, Any]) -> dict[str, Any] | None:
    for obj in iter_tts_objects(save_data.get("ObjectStates", [])):
        if obj.get("GUID") == "664c59" or obj.get("Nickname") == "card_db":
            return obj
    return None


def publish_to_save(payload: dict[str, Any]) -> dict[str, Any]:
    source_json = resolve_path(payload.get("source_json"), DEFAULT_JSON)
    target_save = resolve_path(payload.get("target_tts_save"), DEFAULT_TTS_SAVE)
    carddb = load_json_db(source_json)
    if not carddb:
        raise ValueError(f"No cards found in {source_json}")
    if not target_save.exists():
        raise FileNotFoundError(f"TTS save JSON not found: {target_save}")

    raw = target_save.read_text(encoding="utf-8-sig")
    save_data = json.loads(raw)
    card_db_obj = find_card_db_save_object(save_data)
    if not card_db_obj:
        raise ValueError("Could not find card_db object / GUID 664c59 in the save")

    old_script = card_db_obj.get("LuaScript") or ""
    if "local cardDbImages = {}" not in old_script or "local cardDbMeta = {" not in old_script:
        raise ValueError("The save's card_db object does not look like the expected notecard script")

    card_db_obj["LuaScript"] = rebuild_carddb_lua_text(old_script, carddb)
    backup_path = backup(target_save)
    with target_save.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(save_data, handle, ensure_ascii=False, indent=2)

    result = {
        "source_json": str(source_json),
        "target_tts_save": str(target_save),
        "backup": str(backup_path) if backup_path else "",
        "cards_total": len(carddb),
        "image_rows": sum(1 for row in carddb.values() if row.get("image")),
        "updated_guid": card_db_obj.get("GUID", ""),
        "updated_nickname": card_db_obj.get("Nickname", ""),
    }
    add_history_entry(
        {
            "type": "publish_save",
            "label": target_save.name,
            "settings": {
                "source_json": str(source_json),
                "target_tts_save": str(target_save),
            },
            "result": result,
        }
    )
    return result


def make_variant_key(base_key: str, row: dict[str, Any], used_keys: set[str]) -> str:
    return gen.make_variant_key(base_key, row, used_keys)


def apply_choices(job: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    settings = job["settings"]
    analysis = job["result"]
    target_json = resolve_path(payload.get("target_json") or settings.get("target_json"), DEFAULT_JSON)
    target_lua = resolve_path(payload.get("target_lua") or settings.get("target_lua"), DEFAULT_LUA)
    decisions_path = resolve_path(payload.get("decisions_json"), DEFAULT_COLLISIONS)
    choices = payload.get("choices") or {}
    keep_unselected_as_variants = bool(payload.get("keep_unselected_as_variants"))

    existing = load_json_db(target_json)
    merged = {key: dict(value) for key, value in existing.items()}
    incoming_full = analysis["incoming_full"]
    incoming_by_ref = {entry["ref"]: entry for entry in incoming_full}
    existing_entries = grouped_existing(existing)
    existing_by_ref = {
        entry["ref"]: entry
        for entries in existing_entries.values()
        for entry in entries
    }

    conflict_bases = {conflict["base_key"] for conflict in analysis["conflicts"]}
    added = 0
    replaced = 0
    skipped = 0
    decision_rows: list[dict[str, Any]] = []

    for entry in incoming_full:
        if entry["base_key"] in conflict_bases:
            continue
        key = entry["key"]
        if key not in merged:
            merged[key] = entry["row"]
            added += 1
        else:
            skipped += 1

    for conflict in analysis["conflicts"]:
        base_key = conflict["base_key"]
        selected_ref = choices.get(base_key) or conflict.get("default_ref")
        if selected_ref == "skip":
            skipped += 1
            decision_rows.append({"base_key": base_key, "choice": "skip"})
            continue

        selected = incoming_by_ref.get(selected_ref) or existing_by_ref.get(selected_ref)
        if not selected:
            skipped += 1
            decision_rows.append({"base_key": base_key, "choice": selected_ref, "status": "missing"})
            continue

        for existing_entry in existing_entries.get(base_key, []):
            merged.pop(existing_entry["key"], None)

        merged[base_key] = selected["row"]
        replaced += 1
        decision_rows.append(
            {
                "base_key": base_key,
                "choice": selected_ref,
                "source": selected["source"],
                "uvs_id": selected.get("uvs_id"),
                "image": selected.get("image"),
            }
        )

        if keep_unselected_as_variants:
            used = set(merged.keys())
            for option in conflict["choices"]:
                if option["ref"] == selected_ref:
                    continue
                source = incoming_by_ref.get(option["ref"]) or existing_by_ref.get(option["ref"])
                if not source:
                    continue
                variant_key = make_variant_key(base_key, source["row"], used)
                merged[variant_key] = source["row"]
                used.add(variant_key)
                added += 1

    target_json.parent.mkdir(parents=True, exist_ok=True)
    target_lua.parent.mkdir(parents=True, exist_ok=True)
    decisions_path.parent.mkdir(parents=True, exist_ok=True)

    json_backup = backup(target_json)
    lua_backup = backup(target_lua)
    gen.write_json(str(target_json), merged)
    gen.write_lua(str(target_lua), merged)
    with decisions_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(decision_rows, handle, ensure_ascii=False, indent=2, sort_keys=True)

    result = {
        "cards_total": len(merged),
        "added": added,
        "replaced_conflicts": replaced,
        "skipped": skipped,
        "target_json": str(target_json),
        "target_lua": str(target_lua),
        "decisions_json": str(decisions_path),
        "json_backup": str(json_backup) if json_backup else "",
        "lua_backup": str(lua_backup) if lua_backup else "",
    }
    add_history_entry(
        {
            "type": "apply_choices",
            "label": f"Extension {settings.get('extension_code') or settings.get('extension_id') or ''}".strip(),
            "settings": dict(settings),
            "analysis": analysis,
            "choices": choices,
            "keep_unselected_as_variants": keep_unselected_as_variants,
            "decision_rows": decision_rows,
            "source_history_id": payload.get("history_id") or "",
            "result": result,
        }
    )
    return result


def start_job(settings: dict[str, Any]) -> str:
    job_id = uuid.uuid4().hex
    job = {
        "id": job_id,
        "status": "running",
        "settings": settings,
        "log": [],
        "result": None,
        "error": None,
        "started_at": now(),
    }
    with JOBS_LOCK:
        JOBS[job_id] = job

    def worker() -> None:
        try:
            incoming = scrape_cards(settings, job)
            job["result"] = analyze_cards(settings, incoming)
            job["status"] = "ready"
            job_log(job, "Preview ready")
        except Exception as exc:
            job["status"] = "error"
            job["error"] = f"{exc}\n{traceback.format_exc()}"
            job_log(job, f"Error: {exc}")

    threading.Thread(target=worker, daemon=True).start()
    return job_id


class CardDBHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


class Handler(SimpleHTTPRequestHandler):
    server_version = "CardDBUI/1.0"

    def translate_path(self, path: str) -> str:
        clean = urlparse(path).path.lstrip("/")
        if clean in ("", "cardDB_ui.xml"):
            clean = "cardDB_ui.html"
        return str((APP_DIR / clean).resolve())

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            qs = parse_qs(parsed.query)
            self.send_json(JOBS.get(qs.get("job_id", [""])[0]) or {"status": "missing"})
            return
        if parsed.path == "/api/defaults":
            saves = list_tts_saves()
            self.send_json(
                {
                    "target_json": str(DEFAULT_JSON),
                    "target_lua": str(DEFAULT_LUA),
                    "decisions_json": str(DEFAULT_COLLISIONS),
                    "target_tts_lua": str(DEFAULT_TTS_LUA),
                    "target_tts_save": saves[0]["path"] if saves else "",
                }
            )
            return
        if parsed.path == "/api/saves":
            self.send_json({"saves": list_tts_saves()})
            return
        if parsed.path == "/api/history":
            self.send_json({"history": [summarize_history_entry(entry) for entry in load_history()]})
            return
        if parsed.path == "/api/history-entry":
            qs = parse_qs(parsed.query)
            entry = get_history_entry(qs.get("id", [""])[0])
            if not entry:
                self.send_json({"error": "History entry not found"}, status=404)
                return
            self.send_json(entry)
            return
        return super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        payload = self.read_json()
        if parsed.path == "/api/scrape":
            job_id = start_job(payload)
            self.send_json({"job_id": job_id})
            return
        if parsed.path == "/api/apply":
            job_id = payload.get("job_id")
            job = JOBS.get(job_id)
            if not job or job.get("status") != "ready":
                self.send_json({"error": "Job is not ready"}, status=400)
                return
            try:
                self.send_json(apply_choices(job, payload))
            except Exception as exc:
                self.send_json({"error": str(exc), "traceback": traceback.format_exc()}, status=500)
            return
        if parsed.path == "/api/apply-history":
            entry = get_history_entry(str(payload.get("history_id") or ""))
            if not entry or entry.get("type") != "apply_choices" or not entry.get("analysis"):
                self.send_json({"error": "Apply history entry not found"}, status=404)
                return
            job = {
                "settings": entry.get("settings") or {},
                "result": entry.get("analysis"),
            }
            try:
                self.send_json(apply_choices(job, payload))
            except Exception as exc:
                self.send_json({"error": str(exc), "traceback": traceback.format_exc()}, status=500)
            return
        if parsed.path == "/api/publish":
            try:
                self.send_json(publish_to_tts(payload))
            except Exception as exc:
                self.send_json({"error": str(exc), "traceback": traceback.format_exc()}, status=500)
            return
        if parsed.path == "/api/publish-save":
            try:
                self.send_json(publish_to_save(payload))
            except Exception as exc:
                self.send_json({"error": str(exc), "traceback": traceback.format_exc()}, status=500)
            return
        self.send_json({"error": "Unknown endpoint"}, status=404)

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        if not length:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw)

    def send_json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    import argparse
    import webbrowser

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    server = CardDBHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}/cardDB_ui.xml"
    print(f"CardDB UI running at {url}")
    if not args.no_open:
        webbrowser.open(url)
    server.serve_forever()


if __name__ == "__main__":
    main()
