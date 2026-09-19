"""Build the reviewed UVS Ultra alternate-art runtime catalog.

Only exact, unique name matches are accepted automatically. Ambiguous and
missing records are written to a separate review queue and never become
runtime choices by accident.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


CARD_DB_ROW = re.compile(
    r'^\s*\["(?P<name>(?:\\.|[^"])*)"\]\s*=\s*\{'
    r'.*?uvs_id=(?P<uvs_id>\d+).*?image="(?P<image>[^"]+)"'
)


def normalize_name(value: str) -> str:
    punctuation = {
        0x2018: "'",
        0x2019: "'",
        0x201C: '"',
        0x201D: '"',
    }
    return re.sub(r"\s+", " ", value.translate(punctuation).strip()).casefold()


def unescape_lua(value: str) -> str:
    return value.replace("\\\"", '"').replace("\\\\", "\\")


def load_card_db(path: Path) -> dict[str, list[dict[str, str]]]:
    candidates: dict[str, dict[tuple[str, str], dict[str, str]]] = defaultdict(dict)

    for line in path.read_text(encoding="utf-8").splitlines():
        match = CARD_DB_ROW.match(line)
        if not match:
            continue

        row = {
            "uvsUltraCardId": match.group("uvs_id"),
            "imageUrl": match.group("image"),
        }
        key = normalize_name(unescape_lua(match.group("name")))
        candidates[key][(row["uvsUltraCardId"], row["imageUrl"])] = row

    return {key: list(rows.values()) for key, rows in candidates.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--card-db", required=True, type=Path)
    parser.add_argument(
        "--gallery-manifest",
        type=Path,
        default=Path(__file__).parents[1] / "official-gallery" / "manifest.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("manifest.json"),
    )
    parser.add_argument(
        "--unresolved-output",
        type=Path,
        default=Path(__file__).with_name("unresolved.json"),
    )
    args = parser.parse_args()

    gallery = json.loads(args.gallery_manifest.read_text(encoding="utf-8-sig"))
    card_db = load_card_db(args.card_db)
    cards: dict[str, dict[str, object]] = {}
    unresolved: list[dict[str, object]] = []

    for source in gallery:
        matches = card_db.get(normalize_name(source["cardName"]), [])
        if len(matches) != 1:
            unresolved.append(
                {
                    "officialCardId": source["officialCardId"],
                    "cardName": source["cardName"],
                    "reason": "no_exact_name_match" if not matches else "ambiguous_exact_name_match",
                    "candidates": matches,
                    "sourcePath": f"../official-gallery/{source['localPath']}",
                }
            )
            continue

        match = matches[0]
        card_id = match["uvsUltraCardId"]
        card = cards.setdefault(
            card_id,
            {
                "uvsUltraCardId": card_id,
                "cardName": source["cardName"],
                "variants": [],
            },
        )
        gallery_id = str(source["officialCardId"])
        set_code = str(source.get("officialSetCode") or "").strip()
        card_number = str(source.get("officialCardNumber") or "").strip()
        source_path = f"../official-gallery/{source['localPath']}"
        label_detail = " ".join(part for part in (set_code, card_number) if part)
        label = (
            f"Official Alternate Art ({label_detail})"
            if label_detail
            else f"Official Alternate Art ({gallery_id})"
        )
        card["variants"].append(
            {
                "label": label,
                "qualifier": f"repo/{card_id}-{gallery_id}",
                "officialGalleryId": gallery_id,
                "officialSetCode": set_code or None,
                "officialCardNumber": card_number or None,
                "rarity": source.get("rarity"),
                "sourcePath": source_path,
                "sourceUrl": source["sourceUrl"],
            }
        )

    catalog = {
        "schemaVersion": 1,
        "identityFormat": "repo/{uvsUltraCardId}-{officialGalleryId}",
        "matchingPolicy": "exact_unique_normalized_name",
        "cards": sorted(cards.values(), key=lambda card: int(card["uvsUltraCardId"])),
    }
    review = {
        "schemaVersion": 1,
        "records": unresolved,
    }

    variants = [variant for card in cards.values() for variant in card["variants"]]
    qualifiers = [variant["qualifier"] for variant in variants]
    if len(qualifiers) != len(set(qualifiers)):
        raise RuntimeError("Generated qualifiers are not unique")

    missing_files = [
        variant["sourcePath"]
        for variant in variants
        if not (args.output.parent / variant["sourcePath"]).resolve().is_file()
    ]
    if missing_files:
        raise RuntimeError(f"Missing source images: {missing_files[:5]}")

    args.output.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.unresolved_output.write_text(
        json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"runtime cards={len(cards)} variants={len(variants)} unresolved={len(unresolved)}")


if __name__ == "__main__":
    main()
