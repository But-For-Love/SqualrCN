"""Report remaining ascii literals that sit in user interface display positions.

This catches labels that the general inventory filter skipped, such as single
lowercase words. This is a one-off analysis tool, not part of the shipped
application.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "squalr" / "src"
REPORT_PATH = Path(__file__).resolve().parent / "display_position_report.txt"

DISPLAY_MARKERS = (
    "label(",
    ".text(",
    "RichText::new(",
    "with_tooltip_text(",
    "header:",
    "title:",
    "placeholder",
    "create_header(",
    "ComboBoxView::new(",
    "ComboBoxItemView::new(",
    "ToolbarMenuItemData::new(",
    "GroupBox::new_from_theme(",
    "TextEdit::singleline",
    "window_title",
    "take_over_title",
)

STRING_PATTERN = re.compile(r'"((?:[^"\\\n]|\\.)*)"')

# Internal identifiers and diagnostics that are intentionally left in english.
INTERNAL_PATTERN = re.compile(
    r"(^[a-z0-9_\.]+$|window_|_id$|_salt|view data|view$|ratios|state$|dispatch|failure$|pending$|"
    r"failed|See logs|^expected |^dispatching |#\{|^\{\w+\}|^>|view element|checkstate|"
    r"^\s*$|^[A-Za-z]+_[A-Za-z_]+$)",
    re.IGNORECASE,
)


def contains_cjk(text: str) -> bool:
    """Return true when the text already carries translated characters."""
    return bool(re.search(r"[\u3000-\u9fff\uff00-\uffef]", text))


def main() -> int:
    """Write the display position report."""
    report_lines: list[str] = []
    literal_count = 0

    for source_file in sorted(SOURCE_ROOT.rglob("*.rs")):
        for line_number, line in enumerate(source_file.read_text(encoding="utf-8").splitlines(), start=1):
            if not any(marker in line for marker in DISPLAY_MARKERS):
                continue

            for match in STRING_PATTERN.finditer(line):
                literal = match.group(1)
                if not re.search(r"[A-Za-z]", literal):
                    continue
                if contains_cjk(literal):
                    continue
                if INTERNAL_PATTERN.search(literal):
                    continue
                literal_count += 1
                report_lines.append(f"{source_file.relative_to(ROOT).as_posix()}:{line_number}: {literal}")

    REPORT_PATH.write_text("\n".join([f"remaining display position literals: {literal_count}", "", *report_lines]), encoding="utf-8")
    print(f"remaining display position literals: {literal_count}")
    print(f"report: {REPORT_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
