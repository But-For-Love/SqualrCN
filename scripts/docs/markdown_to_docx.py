"""Convert the Chinese Squalr tutorial from Markdown into a Word document.

Supports the Markdown subset used by the tutorial: headings, paragraphs,
bullet and numbered lists, block quotes, fenced code blocks, pipe tables, and
inline bold/code/link markup. Chinese text is given an explicit east asian font
so that Word and LibreOffice render it consistently.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "docs" / "zh-CN" / "Squalr中文版使用教程.md"
OUTPUT_PATH = ROOT / "docs" / "zh-CN" / "Squalr中文版使用教程.docx"
SCREENSHOT_PATH = ROOT / "docs" / "zh-CN" / "images" / "主界面.png"

BODY_FONT_NAME = "微软雅黑"
CODE_FONT_NAME = "Consolas"
SCREENSHOT_HEADING_MARKER = "界面总览"

INLINE_PATTERN = re.compile(r"(\*\*.+?\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))")


def add_screenshot(document: Document) -> None:
    """Add the annotated main window screenshot with a caption."""
    if not SCREENSHOT_PATH.is_file():
        return

    picture_paragraph = document.add_paragraph()
    picture_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    picture_paragraph.add_run().add_picture(str(SCREENSHOT_PATH), width=Inches(6.4))

    caption_paragraph = document.add_paragraph()
    caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_run = caption_paragraph.add_run("图 1  主界面（默认布局，界面已汉化）")
    set_run_font(caption_run, BODY_FONT_NAME, 9)
    caption_run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)


def set_run_font(
    run,
    font_name: str,
    font_size: int | None = None,
    is_bold: bool = False,
) -> None:
    """Apply a font name (including the east asian variant) to a run."""
    run.font.name = font_name
    if font_size is not None:
        run.font.size = Pt(font_size)
    run.bold = is_bold
    run_properties = run._element.get_or_add_rPr()
    run_fonts = run_properties.find(qn("w:rFonts"))
    if run_fonts is None:
        run_fonts = run_properties.makeelement(qn("w:rFonts"), {})
        run_properties.append(run_fonts)
    run_fonts.set(qn("w:ascii"), font_name)
    run_fonts.set(qn("w:hAnsi"), font_name)
    run_fonts.set(qn("w:eastAsia"), font_name)


def add_inline_runs(
    paragraph,
    text: str,
    font_name: str = BODY_FONT_NAME,
    font_size: int = 10,
) -> None:
    """Add text with inline bold, code, and link markup resolved into runs."""
    for token in INLINE_PATTERN.split(text):
        if not token:
            continue

        if token.startswith("**") and token.endswith("**"):
            set_run_font(paragraph.add_run(token[2:-2]), font_name, font_size, is_bold=True)
        elif token.startswith("`") and token.endswith("`"):
            code_run = paragraph.add_run(token[1:-1])
            set_run_font(code_run, CODE_FONT_NAME, font_size)
            code_run.font.color.rgb = RGBColor(0xB0, 0x30, 0x60)
        elif token.startswith("[") and "](" in token:
            label = token[1 : token.index("](")]
            target = token[token.index("](") + 2 : -1]
            link_run = paragraph.add_run(f"{label}（{target}）" if not target.startswith("#") else label)
            set_run_font(link_run, font_name, font_size)
            link_run.font.color.rgb = RGBColor(0x1E, 0x54, 0x92)
        else:
            set_run_font(paragraph.add_run(token), font_name, font_size)


def configure_document_styles(document: Document) -> None:
    """Configure the base styles so that latin and east asian text both render."""
    normal_style = document.styles["Normal"]
    normal_style.font.name = BODY_FONT_NAME
    normal_style.font.size = Pt(10)
    normal_style.element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT_NAME)

    for style_name, font_size in (("Heading 1", 16), ("Heading 2", 14), ("Heading 3", 12), ("Title", 24)):
        style = document.styles[style_name]
        style.font.name = BODY_FONT_NAME
        style.font.size = Pt(font_size)
        style.font.color.rgb = RGBColor(0x1E, 0x54, 0x92)
        style.element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT_NAME)


def configure_page_layout(document: Document) -> None:
    """Use one inch margins so that tables have a predictable content width."""
    for section in document.sections:
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.top_margin = Inches(0.9)
        section.bottom_margin = Inches(0.9)


def resolve_column_widths(column_count: int) -> list[float]:
    """Return column widths in inches that fit the page content width."""
    # Slightly narrower than the 6.5 inch content width so borders never touch the margin.
    content_width = 6.3

    if column_count <= 1:
        return [content_width]
    if column_count == 2:
        return [1.9, content_width - 1.9]
    if column_count == 3:
        return [1.7, 2.2, content_width - 1.7 - 2.2]

    first_column_width = 1.5
    remaining_width = (content_width - first_column_width) / (column_count - 1)

    return [first_column_width] + [remaining_width] * (column_count - 1)


def parse_table_block(table_lines: list[str]) -> list[list[str]]:
    """Parse pipe table rows into cell values, skipping the separator row."""
    rows: list[list[str]] = []
    for table_line in table_lines:
        stripped_line = table_line.strip().strip("|")
        if re.fullmatch(r"[\s\-:|]+", stripped_line):
            continue
        rows.append([cell.strip() for cell in stripped_line.split("|")])

    return rows


def apply_table_widths(
    table,
    column_widths: list[float],
) -> None:
    """Force a fixed table layout with explicit grid and cell widths.

    LibreOffice keeps the generated `w:tblGrid` widths for fixed layout tables,
    so the grid entries have to be rewritten alongside the cell widths or the
    table overflows the page.
    """
    table_properties = table._tbl.tblPr

    layout_element = table_properties.get_or_add_tblLayout()
    layout_element.set(qn("w:type"), "fixed")

    grid_element = table._tbl.find(qn("w:tblGrid"))
    if grid_element is not None:
        for grid_column, column_width in zip(grid_element.findall(qn("w:gridCol")), column_widths):
            grid_column.set(qn("w:w"), str(int(column_width * 1440)))


def add_table(document: Document, rows: list[list[str]]) -> None:
    """Add a formatted table from parsed pipe rows."""
    if not rows:
        return

    column_count = max(len(row) for row in rows)
    column_widths = resolve_column_widths(column_count)
    table = document.add_table(rows=0, cols=column_count)
    table.style = "Table Grid"

    for row_index, row in enumerate(rows):
        table_row = table.add_row()
        for column_index in range(column_count):
            cell = table_row.cells[column_index]
            cell.width = Inches(column_widths[column_index])
            cell.text = ""
            paragraph = cell.paragraphs[0]
            cell_text = row[column_index] if column_index < len(row) else ""
            add_inline_runs(paragraph, cell_text, font_size=9)
            if row_index == 0:
                for run in paragraph.runs:
                    run.bold = True

    apply_table_widths(table, column_widths)


def convert(markdown_text: str) -> Document:
    """Convert the markdown tutorial into a Word document."""
    document = Document()
    configure_document_styles(document)
    configure_page_layout(document)
    lines = markdown_text.splitlines()

    paragraph_lines: list[str] = []
    table_lines: list[str] = []
    code_lines: list[str] = []
    is_in_code_block = False
    screenshot_inserted = False

    def flush_paragraph() -> None:
        if not paragraph_lines:
            return
        joined_text = " ".join(paragraph_lines).strip()
        paragraph_lines.clear()
        if not joined_text:
            return
        paragraph = document.add_paragraph()
        add_inline_runs(paragraph, joined_text)

    def flush_table() -> None:
        if not table_lines:
            return
        rows = parse_table_block(table_lines)
        table_lines.clear()
        add_table(document, rows)
        document.add_paragraph()

    def flush_code() -> None:
        if not code_lines:
            return
        code_text = "\n".join(code_lines)
        code_lines.clear()
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.left_indent = Inches(0.2)
        code_run = paragraph.add_run(code_text)
        set_run_font(code_run, CODE_FONT_NAME, 9)
        code_run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    for line in lines:
        stripped_line = line.rstrip()

        if stripped_line.startswith("```"):
            flush_paragraph()
            flush_table()
            if is_in_code_block:
                flush_code()
            is_in_code_block = not is_in_code_block
            continue

        if is_in_code_block:
            code_lines.append(stripped_line)
            continue

        if stripped_line.startswith("|"):
            flush_paragraph()
            table_lines.append(stripped_line)
            continue

        flush_table()

        if not stripped_line.strip():
            flush_paragraph()
            continue

        if stripped_line.startswith("#"):
            flush_paragraph()
            heading_match = re.match(r"^(#+)\s*(.*)$", stripped_line)
            if heading_match:
                heading_level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()
                if heading_level == 1:
                    heading = document.add_heading(heading_text, level=0)
                else:
                    heading = document.add_heading(heading_text, level=min(heading_level - 1, 4))
                for run in heading.runs:
                    set_run_font(run, BODY_FONT_NAME, None, is_bold=True)

                if not screenshot_inserted and SCREENSHOT_HEADING_MARKER in heading_text:
                    add_screenshot(document)
                    screenshot_inserted = True
            continue

        if stripped_line.startswith("> "):
            flush_paragraph()
            quote_paragraph = document.add_paragraph()
            quote_paragraph.paragraph_format.left_indent = Inches(0.3)
            add_inline_runs(quote_paragraph, stripped_line[2:].strip(), font_size=9)
            for run in quote_paragraph.runs:
                run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
            continue

        if re.match(r"^[-*]\s+", stripped_line.strip()):
            flush_paragraph()
            indent_level = (len(stripped_line) - len(stripped_line.lstrip())) // 2
            list_style = "List Bullet" if indent_level == 0 else f"List Bullet {min(indent_level + 1, 3)}"
            list_paragraph = document.add_paragraph(style=list_style)
            add_inline_runs(list_paragraph, re.sub(r"^[-*]\s+", "", stripped_line.strip()))
            continue

        if re.match(r"^\d+\.\s+", stripped_line.strip()):
            flush_paragraph()
            indent_level = (len(stripped_line) - len(stripped_line.lstrip())) // 2
            list_style = "List Number" if indent_level == 0 else f"List Number {min(indent_level + 1, 3)}"
            list_paragraph = document.add_paragraph(style=list_style)
            add_inline_runs(list_paragraph, re.sub(r"^\d+\.\s+", "", stripped_line.strip()))
            continue

        if stripped_line.strip() in ("---", "***"):
            flush_paragraph()
            continue

        paragraph_lines.append(stripped_line.strip())

    flush_paragraph()
    flush_table()
    flush_code()

    return document


def main() -> int:
    """Run the conversion."""
    markdown_text = SOURCE_PATH.read_text(encoding="utf-8")
    document = convert(markdown_text)
    document.save(OUTPUT_PATH)
    print(f"wrote: {OUTPUT_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
