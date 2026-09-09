"""
cardDB_generator.py

Scrapes UVS Ultra listing pages and showcard pages, then writes:
- Lua table keyed by normalized card name
- JSON mirror for downstream merging
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import requests
import urllib3

BASE = "https://uvsultra.online/"
LISTING_URL = urljoin(BASE, "listing_cards.php")
KNOWN_TYPES = [
    "Character",
    "Attack",
    "Foundation",
    "Action",
    "Asset",
    "Backup",
    "Stage",
    "Token",
]

RE_SHOWCARD = re.compile(r'(?:href|colorbox)\s*=\s*["\'][^"\']*(?:(showcard|card)\.php\?id=(\d+))', re.I)
RE_TITLE = re.compile(r"<h1[^>]*>\s*(.*?)\s*</h1>", re.I | re.S)
RE_PREVIEW_SRC = re.compile(
    r'<div class="card_image">\s*<img[^>]*src="([^"]+)"[^>]*class="preview_image"',
    re.I | re.S,
)
RE_CD1 = re.compile(r'<div class="card_division cd1">(.*?)</div>', re.I | re.S)
RE_ATK = re.compile(
    r"Attack\s*:\s*([0-9Xx]+)\s*"
    r"<img[^>]*title\s*=\s*\"(low|mid|high)\"[^>]*>\s*"
    r"/\s*([0-9Xx]+)",
    re.I | re.S,
)
RE_ATK_TEXT = re.compile(
    r"Attack\s*:\s*([0-9Xx]+)\s*(low|mid|high)\s*/\s*([0-9Xx]+)",
    re.I | re.S,
)
RE_VIT = re.compile(r"Vitality\s*:\s*([0-9]+)", re.I)
RE_LUA_UVS_ID = re.compile(r'uvs_id\s*=\s*(\d+)', re.I)
RE_LUA_IMAGE_ROW = re.compile(r'^cardDbImages\["((?:\\.|[^"])*)"\]\s*=\s*"', re.M)


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def clean_html_text(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    s = (
        s.replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&#039;", "'")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
    )
    return re.sub(r"\s+", " ", s).strip()


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def lua_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def lua_unescape(s: str) -> str:
    return s.replace('\\"', '"').replace("\\\\", "\\")


def load_seed_knowns(seed_lua_path: str) -> tuple[set[int], set[str], dict[str, set[str]]]:
    if not os.path.isfile(seed_lua_path):
        return set(), set(), {}

    text = open(seed_lua_path, "r", encoding="utf-8").read()
    known_ids = {int(m.group(1)) for m in RE_LUA_UVS_ID.finditer(text)}
    known_image_names: set[str] = set()
    seed_images_by_name: dict[str, set[str]] = {}
    for match in re.finditer(
        r'^cardDbImages\["((?:\\.|[^"])*)"\]\s*=\s*"([^"]*)"',
        text,
        re.M,
    ):
        key = normalize_name(lua_unescape(match.group(1)))
        known_image_names.add(key)
        seed_images_by_name.setdefault(key, set()).add(match.group(2))
    return known_ids, known_image_names, seed_images_by_name


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "uvs-tts-carddb-generator/2.0",
            "X-Requested-With": "XMLHttpRequest",
        }
    )
    return session


def build_listing_form(search_format: str, page: int, extension_id: str | None = None) -> dict[str, str]:
    form = {
        "name": "",
        "card_text": "",
        "format": search_format,
        "spotlightDD": "aot",
        "difficulty_operand": "=",
        "difficulty": "",
        "keyword_text": "",
        "bm_operand": "=",
        "block": "",
        "as_operand": "=",
        "speed": "",
        "ad_operand": "=",
        "damage": "",
        "ac_operand": "=",
        "ability_count": "",
        "kc_operand": "=",
        "keyword_count": "",
        "v_operand": "=",
        "vitality": "",
        "custom_format": "",
        "page": str(page),
    }
    if extension_id:
        form["extension[]"] = str(extension_id)
    return form


def fetch_listing(
    session: requests.Session,
    search_format: str,
    page: int,
    extension_id: str | None = None,
) -> str:
    res = session.post(
        LISTING_URL,
        data=build_listing_form(search_format, page, extension_id),
        timeout=30,
    )
    res.raise_for_status()
    return res.text


def extract_showcards(html: str) -> dict[int, str]:
    out: dict[int, str] = {}
    for page_name, card_id in RE_SHOWCARD.findall(html):
        out[int(card_id)] = f"{page_name}.php?id={card_id}"
    return out


def fetch_showcard(session: requests.Session, rel: str) -> str:
    url = urljoin(BASE, rel)
    res = session.get(url, timeout=30)
    res.raise_for_status()
    return res.text


def parse_type_from_cd1(cd1_html: str) -> str:
    plain_lines = [clean_html_text(x) for x in re.split(r"<br\s*/?>", cd1_html, flags=re.I)]
    for line in plain_lines:
        for t in KNOWN_TYPES:
            if line == t:
                return t
    return ""


def parse_showcard(html: str, uvs_id: int, search_format: str) -> dict[str, Any]:
    title_match = RE_TITLE.search(html)
    name = clean_html_text(title_match.group(1)) if title_match else f"ID {uvs_id}"

    image_url = None
    img_match = RE_PREVIEW_SRC.search(html)
    if img_match:
        raw = img_match.group(1).strip()
        image_url = urljoin(BASE, raw)
        image_url = re.sub(r"\?.*$", "", image_url)
        image_url = re.sub(r"-preview(?=\.[A-Za-z0-9]+$)", "", image_url)

    card_type = ""
    cd1 = RE_CD1.search(html)
    if cd1:
        card_type = parse_type_from_cd1(cd1.group(1))

    speed: int | str | None = None
    damage: int | str | None = None
    zone: str | None = None
    atk = RE_ATK.search(html) or RE_ATK_TEXT.search(html)
    if atk:
        speed_raw = atk.group(1).upper()
        zone = atk.group(2).lower()
        damage_raw = atk.group(3).upper()
        speed = int(speed_raw) if speed_raw.isdigit() else speed_raw
        damage = int(damage_raw) if damage_raw.isdigit() else damage_raw

    vitality = None
    vit = RE_VIT.search(html)
    if vit:
        vitality = int(vit.group(1))

    out: dict[str, Any] = {
        "uvs_id": uvs_id,
        "type": card_type,
    }
    out[search_format] = True
    if image_url:
        out["image"] = image_url
    if speed is not None:
        out["speed"] = speed
    if damage is not None:
        out["damage"] = damage
    if zone is not None:
        out["zone"] = zone
    if vitality is not None:
        out["vitality"] = vitality

    return {"name": name, "data": out}


def write_lua(path: str, carddb: dict[str, dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("return {\n")
        for key in sorted(carddb.keys()):
            row = carddb[key]
            parts = []
            for field in sorted(row.keys(), key=lambda x: (x != "uvs_id", x)):
                value = row[field]
                if isinstance(value, bool):
                    parts.append(f"{field}={'true' if value else 'false'}")
                elif isinstance(value, int):
                    parts.append(f"{field}={value}")
                else:
                    parts.append(f'{field}="{lua_escape(str(value))}"')
            f.write(f'  ["{lua_escape(key)}"] = {{ {", ".join(parts)} }},\n')
        f.write("}\n")


def write_json(path: str, carddb: dict[str, dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(carddb, f, ensure_ascii=False, indent=2, sort_keys=True)


def image_identity(row: dict[str, Any]) -> str:
    return str(row.get("image") or "")


def row_matches_extension(row: dict[str, Any], extension_code: str | None) -> bool:
    if not extension_code:
        return True
    image = str(row.get("image") or "").lower()
    needle = f"/images/extensions/{extension_code.lower()}/"
    return needle in image


def make_variant_key(base_key: str, row: dict[str, Any], used_keys: set[str]) -> str:
    uvs_id = row.get("uvs_id")
    suffix = f" [uvs_id {uvs_id}]" if uvs_id is not None else " [variant]"
    candidate = f"{base_key}{suffix}"
    if candidate not in used_keys:
        return candidate

    idx = 2
    while True:
        candidate = f"{base_key}{suffix} {idx}"
        if candidate not in used_keys:
            return candidate
        idx += 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", choices=["standard", "legacy"], default="legacy")
    parser.add_argument("--max-pages", type=int, default=300)
    parser.add_argument("--stop-empty-pages", type=int, default=2)
    parser.add_argument("--sleep-listing", type=float, default=0.15)
    parser.add_argument("--sleep-showcard", type=float, default=0.03)
    parser.add_argument("--out-lua", default=None)
    parser.add_argument("--out-json", default=None)
    parser.add_argument("--out-collisions", default=None)
    parser.add_argument("--seed-lua", default=".tts/bundled/card_db.664c59.lua")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument(
        "--extension-code",
        default=None,
        help="Only write rows whose image URL belongs to this UVS Ultra extension code, e.g. tk802.",
    )
    parser.add_argument(
        "--extension-id",
        default=None,
        help="Filter UVS Ultra listing results by numeric extension id, e.g. 137.",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification for sources with broken local trust chains.",
    )
    args = parser.parse_args()

    script_dir = os.path.abspath(os.path.dirname(__file__))
    project_dir = (
        os.path.abspath(os.path.join(script_dir, os.pardir))
        if os.path.basename(script_dir).lower() == "uvs_tts_card_updater"
        else script_dir
    )
    out_lua = args.out_lua or os.path.join(project_dir, f"cardDB_{args.format}.lua")
    out_json = args.out_json or os.path.join(project_dir, f"cardDB_{args.format}.json")
    out_collisions = args.out_collisions or os.path.join(
        project_dir, f"cardDB_{args.format}_name_collisions.json"
    )
    out_log = os.path.join(project_dir, "cardDB_runlog.txt")

    def log(msg: str) -> None:
        line = f"[{now()}] {msg}"
        print(line)
        with open(out_log, "a", encoding="utf-8", newline="\n") as lf:
            lf.write(line + "\n")

    with open(out_log, "w", encoding="utf-8", newline="\n") as lf:
        lf.write("")

    log(f"Start format={args.format} max_pages={args.max_pages}")
    session = make_session()
    if args.insecure:
        session.verify = False
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        log("TLS certificate verification disabled (--insecure)")
    known_ids: set[int] = set()
    known_image_names: set[str] = set()
    seed_images_by_name: dict[str, set[str]] = {}
    if args.skip_existing:
        seed_path = args.seed_lua
        if not os.path.isabs(seed_path):
            seed_path = os.path.abspath(os.path.join(project_dir, seed_path))
        known_ids, known_image_names, seed_images_by_name = load_seed_knowns(seed_path)
        log(
            f"Seed loaded from {seed_path} "
            f"(known ids={len(known_ids)}, known image names={len(known_image_names)})"
        )

    all_showcards: dict[int, str] = {}
    empty_pages = 0
    for page in range(args.max_pages):
        html = fetch_listing(session, args.format, page, args.extension_id)
        found = extract_showcards(html)
        log(f"listing page={page + 1} showcards={len(found)}")
        if not found:
            empty_pages += 1
            if empty_pages >= args.stop_empty_pages:
                log(f"stopping after {empty_pages} empty pages")
                break
        else:
            empty_pages = 0
            all_showcards.update(found)
        time.sleep(args.sleep_listing)

    if not all_showcards:
        raise RuntimeError("No showcards found for selected format.")

    log(f"Total unique showcards={len(all_showcards)}")

    carddb: dict[str, dict[str, Any]] = {}
    image_key_by_name: dict[str, dict[str, str]] = {}
    name_collisions: list[dict[str, Any]] = []
    skipped_existing_by_id = 0
    skipped_existing_by_name = 0
    collapsed_same_image = 0
    preserved_different_image = 0
    considered = 0
    for idx, (cid, rel) in enumerate(sorted(all_showcards.items()), start=1):
        if args.skip_existing and cid in known_ids:
            skipped_existing_by_id += 1
            continue

        html = fetch_showcard(session, rel)
        parsed = parse_showcard(html, cid, args.format)
        key = normalize_name(parsed["name"])

        row = parsed["data"]
        if not row_matches_extension(row, args.extension_code):
            continue

        row_image = image_identity(row)
        seed_images = seed_images_by_name.get(key, set()) if args.skip_existing else set()
        if seed_images and row_image in seed_images:
            skipped_existing_by_name += 1
            continue

        seen_images = image_key_by_name.setdefault(key, {})
        if args.skip_existing and seed_images:
            final_key = make_variant_key(key, row, set(carddb.keys()) | known_image_names)
            seen_images[row_image] = final_key
            preserved_different_image += 1
            name_collisions.append(
                {
                    "base_key": key,
                    "chosen_key": final_key,
                    "status": "preserved_different_image_from_seed",
                    "uvs_id": row.get("uvs_id"),
                    "image": row.get("image"),
                    "existing_seed_images": sorted(seed_images),
                }
            )
        elif not seen_images:
            final_key = key
            seen_images[row_image] = final_key
        elif row_image in seen_images:
            final_key = seen_images[row_image]
            collapsed_same_image += 1
            name_collisions.append(
                {
                    "base_key": key,
                    "chosen_key": final_key,
                    "status": "collapsed_same_image",
                    "uvs_id": row.get("uvs_id"),
                    "image": row.get("image"),
                    "existing_uvs_id": carddb[final_key].get("uvs_id"),
                    "existing_image": carddb[final_key].get("image"),
                }
            )
            considered += 1
            if idx % 200 == 0 or idx == len(all_showcards):
                log(f"parsed {idx}/{len(all_showcards)}")
            time.sleep(args.sleep_showcard)
            continue
        else:
            final_key = make_variant_key(key, row, set(carddb.keys()))
            seen_images[row_image] = final_key
            preserved_different_image += 1
            name_collisions.append(
                {
                    "base_key": key,
                    "chosen_key": final_key,
                    "status": "preserved_different_image",
                    "uvs_id": row.get("uvs_id"),
                    "image": row.get("image"),
                    "existing_variants": [
                        {
                            "key": existing_key,
                            "uvs_id": carddb[existing_key].get("uvs_id"),
                            "image": carddb[existing_key].get("image"),
                        }
                        for existing_key in seen_images.values()
                        if existing_key in carddb
                    ],
                }
            )

        carddb[final_key] = row
        considered += 1
        if idx % 200 == 0 or idx == len(all_showcards):
            log(f"parsed {idx}/{len(all_showcards)}")
        time.sleep(args.sleep_showcard)

    write_lua(out_lua, carddb)
    write_json(out_json, carddb)
    with open(out_collisions, "w", encoding="utf-8", newline="\n") as f:
        json.dump(name_collisions, f, ensure_ascii=False, indent=2, sort_keys=True)
    log(
        f"Skip summary: by id={skipped_existing_by_id}, "
        f"by name={skipped_existing_by_name}, fetched new={considered}"
    )
    log(
        "Same-name summary: "
        f"preserved different-image rows={preserved_different_image}, "
        f"collapsed same-image rows={collapsed_same_image}"
    )
    log(f"Wrote Lua:  {out_lua}")
    log(f"Wrote JSON: {out_json}")
    log(f"Wrote collisions: {out_collisions}")
    log(f"Done cards={len(carddb)}")


if __name__ == "__main__":
    main()
