"""Apply the Chinese translation table to the Squalr GUI sources.

The script scans every Rust source file with a small Rust-aware scanner so that
comments are never touched, then replaces the contents of normal string
literals whose exact source text is a key in the translation table. This is a
one-off tool, not part of the shipped application.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "squalr" / "src"
TRANSLATION_PATH = Path(__file__).resolve().parent / "translations.json"
APPLIED_REPORT_PATH = Path(__file__).resolve().parent / "applied_report.txt"


def scan_string_spans(text: str) -> list[tuple[int, int, str]]:
    """Return (content_start, content_end, raw_content) for every normal string literal."""
    spans: list[tuple[int, int, str]] = []
    offset = 0
    length = len(text)

    while offset < length:
        character = text[offset]

        if character == "/" and offset + 1 < length and text[offset + 1] == "/":
            while offset < length and text[offset] != "\n":
                offset += 1
            continue

        if character == "/" and offset + 1 < length and text[offset + 1] == "*":
            nesting_depth = 1
            offset += 2
            while offset < length and nesting_depth > 0:
                if text[offset] == "/" and offset + 1 < length and text[offset + 1] == "*":
                    nesting_depth += 1
                    offset += 2
                elif text[offset] == "*" and offset + 1 < length and text[offset + 1] == "/":
                    nesting_depth -= 1
                    offset += 2
                else:
                    offset += 1
            continue

        # Raw string literals are skipped entirely because they are never display text here.
        is_raw_candidate = character == "r" or (character == "b" and offset + 1 < length and text[offset + 1] == "r")
        if is_raw_candidate and not (offset > 0 and (text[offset - 1].isalnum() or text[offset - 1] == "_")):
            raw_start = offset + (2 if character == "b" else 1)
            hash_count = 0
            while raw_start + hash_count < length and text[raw_start + hash_count] == "#":
                hash_count += 1
            if raw_start + hash_count < length and text[raw_start + hash_count] == '"':
                terminator = '"' + ("#" * hash_count)
                literal_end = text.find(terminator, raw_start + hash_count + 1)
                if literal_end == -1:
                    break
                offset = literal_end + len(terminator)
                continue

        is_byte_string = False
        if character == "b" and offset + 1 < length and text[offset + 1] == '"':
            is_byte_string = True
            offset += 1
            character = '"'

        if character == '"':
            content_start = offset + 1
            cursor = content_start
            while cursor < length and text[cursor] != '"':
                if text[cursor] == "\\" and cursor + 1 < length:
                    cursor += 2
                    continue
                if text[cursor] == "\n":
                    break
                cursor += 1
            if cursor < length and text[cursor] == '"' and not is_byte_string:
                spans.append((content_start, cursor, text[content_start:cursor]))
            offset = cursor + 1
            continue

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

    return spans


def escape_for_rust_literal(translated_text: str) -> str:
    """Escape a translated string so that it is a valid Rust string literal body."""
    return translated_text.replace("\\", "\\\\").replace('"', '\\"')


def main() -> int:
    """Apply the translation table and report what happened."""
    translations: dict[str, str] = json.loads(TRANSLATION_PATH.read_text(encoding="utf-8"))
    applied_counts: Counter[str] = Counter()
    changed_file_count = 0
    replacement_count = 0

    for source_file in sorted(SOURCE_ROOT.rglob("*.rs")):
        text = source_file.read_text(encoding="utf-8")
        spans = scan_string_spans(text)
        if not spans:
            continue

        replacements = [
            (content_start, content_end, translations[raw_content])
            for content_start, content_end, raw_content in spans
            if raw_content in translations and raw_content != translations[raw_content]
        ]
        if not replacements:
            continue

        rebuilt_text: list[str] = []
        cursor = 0
        for content_start, content_end, translated_text in replacements:
            rebuilt_text.append(text[cursor:content_start])
            rebuilt_text.append(escape_for_rust_literal(translated_text))
            cursor = content_end
            applied_counts[text[content_start:content_end]] += 1
            replacement_count += 1
        rebuilt_text.append(text[cursor:])

        source_file.write_text("".join(rebuilt_text), encoding="utf-8")
        changed_file_count += 1

    unused_keys = sorted(key for key in translations if applied_counts[key] == 0)

    report_lines = [
        f"changed files: {changed_file_count}",
        f"replacements: {replacement_count}",
        f"distinct translated literals: {len(applied_counts)}",
        f"unused translation keys: {len(unused_keys)}",
        "",
        "=== unused translation keys",
        *unused_keys,
        "",
        "=== applied literals",
        *[f"{count}\t{literal}" for literal, count in sorted(applied_counts.items(), key=lambda item: (-item[1], item[0]))],
    ]
    APPLIED_REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"changed files: {changed_file_count}")
    print(f"replacements: {replacement_count}")
    print(f"distinct translated literals: {len(applied_counts)}")
    print(f"unused translation keys: {len(unused_keys)}")
    print(f"report: {APPLIED_REPORT_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
