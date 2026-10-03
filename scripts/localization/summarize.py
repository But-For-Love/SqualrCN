"""Summarize the extracted literal inventory into reviewable text reports.

This is a one-off analysis tool, not part of the shipped application.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

WORK_ROOT = Path(__file__).resolve().parent
INVENTORY_PATH = WORK_ROOT / "strings.json"
UNIQUE_REPORT_PATH = WORK_ROOT / "unique_literals.txt"
FILE_REPORT_PATH = WORK_ROOT / "literals_by_file.txt"


def main() -> int:
    """Write frequency-sorted and file-grouped reports."""
    inventory: dict[str, list[dict[str, object]]] = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))

    counter: Counter[str] = Counter()
    for entries in inventory.values():
        for entry in entries:
            counter[str(entry["literal"])] += 1

    lines = [f"{count}\t{literal}" for literal, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))]
    UNIQUE_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

    file_lines: list[str] = []
    for relative_path, entries in sorted(inventory.items()):
        file_lines.append(f"=== {relative_path} ({len(entries)})")
        for entry in entries:
            file_lines.append(f"  {entry['line']}: {entry['literal']}")
    FILE_REPORT_PATH.write_text("\n".join(file_lines), encoding="utf-8")

    print(f"unique: {len(counter)}")
    print(f"unique report: {UNIQUE_REPORT_PATH}")
    print(f"file report: {FILE_REPORT_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
