#!/usr/bin/env python3
"""Convert an .apkg made by this tool into Cadence card packs (.cdc).

Cadence (https://github.com/Batpapa/Cadence) has no front/back: it always shows
a card's name, tags and attachments while reviewing. So each card is named with
a random hash (also used as the mp3 filename), the real name goes into the
card's aliases (searchable in the library, not shown during review), and name,
key and rhythm sit behind a "Show answer" toggle in the notes.

Packs are split around 125 MB of audio each, since a single huge JSON file can
exceed what a browser is able to load.

usage: python anki2cdc.py irish_music.apkg [--tag irish_music] [--out-dir .]
"""

import argparse
import base64
import html
import json
import re
import sqlite3
import tempfile
import uuid
import zipfile
from pathlib import Path

SCHEMA_VERSION = 9
MAX_RAW_BYTES = 125 * 1024 * 1024  # per pack; base64 adds a third


def field(pattern: str, text: str) -> str:
    m = re.search(pattern, text, re.S)
    return html.unescape(m.group(1)).strip() if m else ""


def read_cards(src: Path, tag: str) -> list[dict]:
    media = {v: k for k, v in json.loads((src / "media").read_text()).items()}
    db = sqlite3.connect(f"file:{src / 'collection.anki2'}?mode=ro", uri=True)
    cards = []
    for (flds,) in db.execute("select flds from notes order by id"):
        # Fields can be on either side depending on the chosen card layout.
        text = flds.replace("\x1f", "\n")
        sound = field(r"\[sound:(.+?)\]", text)
        name = field(r"field-name'><b>(.*?)</b>", text)
        key = field(r"<b>Key:</b>(.*?)</div>", text)
        rhythm = field(r"<b>Rhythm:</b>(.*?)</div>", text)
        hashed = uuid.uuid4().hex[:8]
        answer = [f"**Name:** {name}"] if name else []
        answer += [f"**Key:** {key}"] if key else []
        answer += [f"**Rhythm:** {rhythm}"] if rhythm else []
        attachments = []
        if sound and sound in media:
            raw = (src / media[sound]).read_bytes()
            attachments.append(
                {
                    "type": "file",
                    "name": f"{hashed}.mp3",
                    "mimeType": "audio/mpeg",
                    "data": base64.b64encode(raw).decode(),
                }
            )
        cards.append(
            {
                "id": str(uuid.uuid4()),
                "guid": str(uuid.uuid4()),
                "name": hashed,
                **({"aliases": [name]} if name else {}),
                "type": "tune",
                "defaultImportance": 1,
                "tags": [tag],
                "content": {
                    "notes": "<details><summary>Show answer</summary>\n\n"
                    + "  \n".join(answer)
                    + "\n\n</details>",
                    "attachments": attachments,
                },
            }
        )
    db.close()
    return cards


def split_packs(cards: list[dict]) -> list[list[dict]]:
    packs: list[list[dict]] = [[]]
    size = 0
    for card in cards:
        n = sum(len(a["data"]) * 3 // 4 for a in card["content"]["attachments"])
        if packs[-1] and size + n > MAX_RAW_BYTES:
            packs.append([])
            size = 0
        size += n
        packs[-1].append(card)
    return packs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("apkg", type=Path)
    parser.add_argument("--tag", help="tag put on every card (default: apkg name)")
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    args = parser.parse_args()
    tag = args.tag or args.apkg.stem
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(args.apkg) as z:
            z.extractall(tmp)
        packs = split_packs(read_cards(Path(tmp), tag))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for i, cards in enumerate(packs, 1):
        suffix = f"-{i}of{len(packs)}" if len(packs) > 1 else ""
        out = args.out_dir / f"{args.apkg.stem}{suffix}.cdc"
        out.write_text(json.dumps({"schemaVersion": SCHEMA_VERSION, "cards": cards}))
        print(f"{out}: {len(cards)} cards, {out.stat().st_size / 1e6:.0f} MB")


if __name__ == "__main__":
    main()
