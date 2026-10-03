"""Extract Rust string literals from the Squalr GUI crate for localization review.

A small Rust-aware scanner skips comments so that commented out code and doc
comments never show up in the inventory. This is a one-off analysis tool, not
part of the shipped application.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "squalr" / "src"
OUTPUT_PATH = Path(__file__).resolve().parent / "strings.json"

# Literals that look like machine identifiers rather than display text.
IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9_\.\-]*$")

NON_DISPLAY_PREFIXES = (
    "window_",
    "resize_",
    "dock",
)

LOG_MARKERS = (
    "failed to ",
    "unable to ",
    "could not ",
    "timed out",
    "is not set",
    "was not found",
    "not available",
    "does not support",
    "is required",
    "lock",
)


def scan_file(file_path: Path) -> list[dict[str, object]]:
    """Scan a Rust file and return every string literal with its line number."""
    text = file_path.read_text(encoding="utf-8")
    literals: list[dict[str, object]] = []
    line_number = 1
    offset = 0
    length = len(text)

    while offset < length:
        character = text[offset]

        if character == "\n":
            line_number += 1
            offset += 1
            continue

        # Line comment.
        if character == "/" and offset + 1 < length and text[offset + 1] == "/":
            while offset < length and text[offset] != "\n":
                offset += 1
            continue

        # Block comment, which may nest in Rust.
        if character == "/" and offset + 1 < length and text[offset + 1] == "*":
            nesting_depth = 1
            offset += 2
            while offset < length and nesting_depth > 0:
                if text[offset] == "\n":
                    line_number += 1
                    offset += 1
                elif text[offset] == "/" and offset + 1 < length and text[offset + 1] == "*":
                    nesting_depth += 1
                    offset += 2
                elif text[offset] == "*" and offset + 1 < length and text[offset + 1] == "/":
                    nesting_depth -= 1
                    offset += 2
                else:
                    offset += 1
            continue

        # Raw string literal: r"..." / r#"..."# / br#"..."#.
        is_raw_candidate = character == "r" or (character == "b" and offset + 1 < length and text[offset + 1] == "r")
        if is_raw_candidate and not (offset > 0 and (text[offset - 1].isalnum() or text[offset - 1] == "_")):
            raw_start = offset + (2 if character == "b" else 1)
            hash_count = 0
            while raw_start + hash_count < length and text[raw_start + hash_count] == "#":
                hash_count += 1
            if raw_start + hash_count < length and text[raw_start + hash_count] == '"':
                terminator = '"' + ("#" * hash_count)
                literal_start = raw_start + hash_count + 1
                literal_end = text.find(terminator, literal_start)
                if literal_end == -1:
                    break
                literal = text[literal_start:literal_end]
                literals.append(
                    {
                        "line": line_number,
                        "literal": literal,
                        "byte_string": character == "b",
                    }
                )
                line_number += text.count("\n", offset, literal_end + len(terminator))
                offset = literal_end + len(terminator)
                continue

        # Byte string literal: b"...".
        if character == "b" and offset + 1 < length and text[offset + 1] == '"':
            offset += 1
            character = '"'

        # Normal string literal.
        if character == '"':
            literal_characters: list[str] = []
            offset += 1
            while offset < length and text[offset] != '"':
                if text[offset] == "\\" and offset + 1 < length:
                    literal_characters.append(text[offset])
                    literal_characters.append(text[offset + 1])
                    if text[offset + 1] == "\n":
                        line_number += 1
                    offset += 2
                    continue
                if text[offset] == "\n":
                    break
                literal_characters.append(text[offset])
                offset += 1
            offset += 1
            literals.append(
                {
                    "line": line_number,
                    "literal": "".join(literal_characters),
                    "byte_string": False,
                }
            )
            continue

        # Character literal or lifetime; advance past it so quotes never confuse us.
        if character == "'":
            if offset + 2 < length and text[offset + 2] == "'" and text[offset + 1] != "\\":
                offset += 3
                continue
            if offset + 3 < length and text[offset + 1] == "\\" and text[offset + 3] == "'":
                offset += 4
                continue
            offset += 1
            continue

        offset += 1

    return literals


def is_display_literal(literal: str) -> bool:
    """Heuristically decide whether a literal is user facing display text."""
    if len(literal) < 2 or len(literal) > 160:
        return False
    if "\n" in literal or "\t" in literal:
        return False
    if not any(character.isalpha() for character in literal):
        return False
    if not any(character.isascii() for character in literal):
        return False
    if IDENTIFIER_PATTERN.match(literal):
        return False
    if literal.startswith(NON_DISPLAY_PREFIXES) and IDENTIFIER_PATTERN.match(literal):
        return False
    if literal.startswith(("http://", "https://", "www.")):
        return False
    if literal.startswith("{:") or literal.startswith("{}"):
        return False
    if "::" in literal or ".rs" in literal:
        return False
    # Format strings that are pure plumbing, such as "{} B" are still display
    # text, but diagnostic strings are not.
    lowered = literal.lower()
    if any(marker in lowered for marker in LOG_MARKERS):
        return False
    if " " in literal or literal[0].isupper():
        return True

    return False


def main() -> int:
    """Walk the GUI crate and write a JSON inventory of candidate strings."""
    inventory: dict[str, list[dict[str, object]]] = {}
    total_count = 0

    for source_file in sorted(SOURCE_ROOT.rglob("*.rs")):
        literals = scan_file(source_file)
        entries = [
            {"line": literal["line"], "literal": literal["literal"]}
            for literal in literals
            if not literal["byte_string"] and is_display_literal(str(literal["literal"]))
        ]
        if not entries:
            continue
        inventory[source_file.relative_to(ROOT).as_posix()] = entries
        total_count += len(entries)

    OUTPUT_PATH.write_text(json.dumps(inventory, indent=1, ensure_ascii=False), encoding="utf-8")
    unique_literals = {str(entry["literal"]) for entries in inventory.values() for entry in entries}
    print(f"files: {len(inventory)}")
    print(f"candidate literals: {total_count}")
    print(f"unique candidate literals: {len(unique_literals)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
