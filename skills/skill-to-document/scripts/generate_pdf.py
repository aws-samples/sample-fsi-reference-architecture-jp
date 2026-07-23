#!/usr/bin/env python3
"""Generate PDF from HTML using fpdf2 with Japanese font support.

Usage:
    python generate_pdf.py --input <html_file> --output <output_dir> --skill-name <name>

Parses the HTML document produced by the skill-to-document agent workflow
and renders it as a professionally formatted PDF with embedded Japanese fonts.
"""

import argparse
import os
import platform
import sys
from html.parser import HTMLParser
from pathlib import Path

from fpdf import FPDF


# ---------------------------------------------------------------------------
# Font resolution – OS-native Japanese fonts with fallback
# ---------------------------------------------------------------------------

_FONT_CANDIDATES = {
    "Darwin": [  # macOS
        ("HiraginoSans", "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"),
        ("HiraginoSans", "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"),
        ("HiraMinProN", "/System/Library/Fonts/ヒラギノ明朝 ProN W3.ttc"),
        ("HiraginoSans", "/System/Library/Fonts/HiraginoSans-W3.ttc"),
        ("HiraginoSans", "/System/Library/Fonts/HiraginoSans-W6.ttc"),
    ],
    "Windows": [
        ("YuGothic", "C:/Windows/Fonts/YuGothR.ttc"),
        ("YuGothic", "C:/Windows/Fonts/yugothic.ttf"),
        ("Meiryo", "C:/Windows/Fonts/meiryo.ttc"),
        ("MSGothic", "C:/Windows/Fonts/msgothic.ttc"),
    ],
}

_MONO_CANDIDATES = {
    "Darwin": [
        ("HiraginoSansMono", "/System/Library/Fonts/HiraginoSans-W3.ttc"),
    ],
    "Windows": [
        ("MSGothic", "C:/Windows/Fonts/msgothic.ttc"),
    ],
}


def _find_font(candidates: list[tuple[str, str]]) -> tuple[str, str] | None:
    for name, path in candidates:
        if os.path.exists(path):
            return name, path
    return None


# ---------------------------------------------------------------------------
# Lightweight HTML-to-PDF renderer
# ---------------------------------------------------------------------------

class _State:
    """Mutable rendering state shared across the parser."""

    def __init__(self):
        self.bold = False
        self.italic = False
        self.in_code = False
        self.in_pre = False
        self.in_title_page = False
        self.in_toc = False
        self.in_table = False
        self.in_thead = False
        self.in_th = False
        self.in_td = False
        self.in_li = False
        self.in_blockquote = False
        self.heading_level = 0
        self.list_depth = 0
        self.list_type: list[str] = []  # "ul" or "ol"
        self.list_counters: list[int] = []
        self.table_rows: list[list[str]] = []
        self.current_row: list[str] = []
        self.current_cell = ""
        self.link_href = ""
        self.pending_text = ""
        self.chapter_class = False


class PDFDocument(FPDF):
    """Custom FPDF subclass with Japanese font and styling support."""

    def __init__(self, font_name: str, font_path: str,
                 mono_name: str, mono_path: str):
        super().__init__(orientation="P", unit="mm", format="A4")
        self._ja_font = font_name
        self._mono_font = mono_name

        self.add_font(font_name, "", font_path)
        self.add_font(font_name, "B", font_path)
        self.add_font(font_name, "I", font_path)
        if mono_name != font_name:
            self.add_font(mono_name, "", mono_path)

        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(20, 20, 20)

    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font(self._ja_font, "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, str(self.page_no()), align="C")

    @property
    def ja_font(self):
        return self._ja_font

    @property
    def mono_font(self):
        return self._mono_font


class HTMLToPDFParser(HTMLParser):
    """Parse skill-to-document HTML and render to PDFDocument."""

    # Heading sizes in pt
    _H_SIZES = {1: 20, 2: 16, 3: 14, 4: 12, 5: 11, 6: 10}

    def __init__(self, pdf: PDFDocument, base_dir: str):
        super().__init__()
        self.pdf = pdf
        self.base_dir = base_dir
        self.s = _State()

    # -- helpers --

    def _ensure_page(self):
        if self.pdf.page == 0:
            self.pdf.add_page()

    def _flush_text(self):
        text = self.s.pending_text
        if not text:
            return
        self.s.pending_text = ""

        if self.s.in_table:
            self.s.current_cell += text
            return

        self._ensure_page()

        if self.s.in_pre:
            self.pdf.set_font(self.pdf.mono_font, "", 9)
            self.pdf.multi_cell(0, 5, text)
            return

        style = ""
        if self.s.bold:
            style += "B"
        if self.s.italic:
            style += "I"

        if self.s.heading_level:
            size = self._H_SIZES.get(self.s.heading_level, 10)
            self.pdf.set_font(self.pdf.ja_font, "B", size)
            self.pdf.set_text_color(15, 27, 61)
            self.pdf.multi_cell(0, size * 0.5, text)
            self.pdf.set_text_color(0, 0, 0)
            if self.s.heading_level <= 2:
                self.pdf.set_draw_color(27, 58, 107)
                y = self.pdf.get_y()
                self.pdf.line(20, y, 190, y)
                self.pdf.ln(2)
            return

        if self.s.in_title_page:
            self.pdf.set_font(self.pdf.ja_font, "B", 24)
            self.pdf.set_text_color(15, 27, 61)
            self.pdf.multi_cell(0, 14, text, align="C")
            self.pdf.set_text_color(0, 0, 0)
            return

        if self.s.in_code and not self.s.in_pre:
            self.pdf.set_font(self.pdf.mono_font, "", 9)
            self.pdf.set_fill_color(240, 242, 246)
            tw = self.pdf.get_string_width(text) + 2
            # Check if inline code fits on current line
            remaining = self.pdf.w - self.pdf.r_margin - self.pdf.get_x()
            if tw > remaining:
                self.pdf.ln()
                self.pdf.set_x(self.pdf.l_margin)
            self.pdf.cell(tw, 6, text, fill=True)
            return

        font_size = 10
        self.pdf.set_font(self.pdf.ja_font, style, font_size)

        if self.s.in_li:
            indent = self.pdf.l_margin + (self.s.list_depth) * 6
            self.pdf.set_x(indent)
            w = self.pdf.w - self.pdf.r_margin - indent
            if w < 10:
                self.pdf.ln()
                self.pdf.set_x(indent)
                w = self.pdf.w - self.pdf.r_margin - indent
            self.pdf.multi_cell(w, 6, text)
        elif self.s.in_blockquote:
            self.pdf.set_x(self.pdf.l_margin + 5)
            w = self.pdf.w - self.pdf.r_margin - self.pdf.l_margin - 5
            self.pdf.set_text_color(74, 74, 90)
            self.pdf.multi_cell(w, 6, text)
            self.pdf.set_text_color(0, 0, 0)
        else:
            self.pdf.set_x(self.pdf.l_margin)
            self.pdf.multi_cell(0, 6, text)

    # -- tag handlers --

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        cls = attr.get("class", "")

        if tag == "div" and "title-page" in cls:
            self.s.in_title_page = True
            self.pdf.add_page()
            self.pdf.ln(60)
            return

        if tag == "div" and "toc" in cls:
            self.s.in_toc = True
            return

        if tag == "div" and "chapter" in cls:
            self.s.chapter_class = True
            self.pdf.add_page()
            return

        if tag == "div" and "appendix" in cls:
            self.pdf.add_page()
            return

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._flush_text()
            self.s.heading_level = int(tag[1])
            self.pdf.ln(4)
            return

        if tag == "p":
            self._flush_text()
            return

        if tag == "strong" or tag == "b":
            self._flush_text()
            self.s.bold = True
            return

        if tag == "em" or tag == "i":
            self._flush_text()
            self.s.italic = True
            return

        if tag == "code":
            self._flush_text()
            self.s.in_code = True
            return

        if tag == "pre":
            self._flush_text()
            self.s.in_pre = True
            self.pdf.set_fill_color(240, 242, 246)
            self.pdf.ln(2)
            return

        if tag == "ul":
            self.s.list_depth += 1
            self.s.list_type.append("ul")
            self.s.list_counters.append(0)
            return

        if tag == "ol":
            self.s.list_depth += 1
            self.s.list_type.append("ol")
            self.s.list_counters.append(0)
            return

        if tag == "li":
            self._flush_text()
            self.s.in_li = True
            if self.s.list_type and self.s.list_type[-1] == "ol":
                self.s.list_counters[-1] += 1
                prefix = f"{self.s.list_counters[-1]}. "
            else:
                prefix = "• "
            self.s.pending_text = prefix
            return

        if tag == "blockquote":
            self._flush_text()
            self.s.in_blockquote = True
            self.pdf.set_x(25)
            self.pdf.set_draw_color(27, 58, 107)
            return

        if tag == "table":
            self._flush_text()
            self.s.in_table = True
            self.s.table_rows = []
            return

        if tag == "thead":
            self.s.in_thead = True
            return

        if tag == "tr":
            self.s.current_row = []
            return

        if tag == "th":
            self.s.in_th = True
            self.s.current_cell = ""
            return

        if tag == "td":
            self.s.in_td = True
            self.s.current_cell = ""
            return

        if tag == "img":
            self._flush_text()
            self._ensure_page()
            src = attr.get("src", "")
            img_path = os.path.join(self.base_dir, src) if src else ""
            if img_path and os.path.exists(img_path):
                try:
                    max_w = 170  # mm, within margins
                    self.pdf.image(img_path, w=max_w)
                except Exception:
                    self.pdf.set_font(self.pdf.ja_font, "I", 9)
                    self.pdf.cell(0, 6, f"[画像: {src} — 読み込みエラー]")
            else:
                self.pdf.set_font(self.pdf.ja_font, "I", 9)
                self.pdf.cell(0, 6, f"[画像: {src} — 取得不可]")
            self.pdf.ln(4)
            return

        if tag == "hr":
            self._flush_text()
            self._ensure_page()
            self.pdf.ln(4)
            self.pdf.set_draw_color(197, 205, 217)
            y = self.pdf.get_y()
            self.pdf.line(20, y, 190, y)
            self.pdf.ln(4)
            return

        if tag == "br":
            self._flush_text()
            self.pdf.ln(3)
            return

        if tag == "a":
            self.s.link_href = attr.get("href", "")
            return

    def handle_endtag(self, tag):
        if tag == "div":
            if self.s.in_title_page:
                self.s.in_title_page = False
            if self.s.in_toc:
                self.s.in_toc = False
            if self.s.chapter_class:
                self.s.chapter_class = False
            return

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._flush_text()
            self.s.heading_level = 0
            self.pdf.ln(2)
            return

        if tag == "p":
            self._flush_text()
            self.pdf.ln(3)
            return

        if tag in ("strong", "b"):
            self._flush_text()
            self.s.bold = False
            return

        if tag in ("em", "i"):
            self._flush_text()
            self.s.italic = False
            return

        if tag == "code":
            self._flush_text()
            self.s.in_code = False
            return

        if tag == "pre":
            self._flush_text()
            self.s.in_pre = False
            self.pdf.ln(4)
            return

        if tag in ("ul", "ol"):
            if self.s.list_depth > 0:
                self.s.list_depth -= 1
                self.s.list_type.pop() if self.s.list_type else None
                self.s.list_counters.pop() if self.s.list_counters else None
            self.pdf.ln(2)
            return

        if tag == "li":
            self._flush_text()
            self.s.in_li = False
            return

        if tag == "blockquote":
            self._flush_text()
            self.s.in_blockquote = False
            self.pdf.ln(2)
            return

        if tag == "thead":
            self.s.in_thead = False
            return

        if tag in ("th", "td"):
            self.s.current_row.append(self.s.current_cell.strip())
            self.s.current_cell = ""
            self.s.in_th = False
            self.s.in_td = False
            return

        if tag == "tr":
            if self.s.current_row:
                self.s.table_rows.append(self.s.current_row)
            return

        if tag == "table":
            self._render_table()
            self.s.in_table = False
            self.s.table_rows = []
            return

        if tag == "a":
            self.s.link_href = ""
            return

    def handle_data(self, data):
        if self.s.in_table:
            self.s.current_cell += data
        else:
            self.s.pending_text += data

    def _render_table(self):
        rows = self.s.table_rows
        if not rows:
            return
        num_cols = max(len(r) for r in rows)
        if num_cols == 0:
            return
        self._ensure_page()
        col_w = 170 / num_cols  # distribute evenly within margins

        for i, row in enumerate(rows):
            is_header = i == 0
            if is_header:
                self.pdf.set_font(self.pdf.ja_font, "B", 9)
                self.pdf.set_fill_color(27, 58, 107)
                self.pdf.set_text_color(255, 255, 255)
            else:
                self.pdf.set_font(self.pdf.ja_font, "", 9)
                self.pdf.set_text_color(0, 0, 0)
                if i % 2 == 0:
                    self.pdf.set_fill_color(245, 247, 250)
                else:
                    self.pdf.set_fill_color(255, 255, 255)

            for j in range(num_cols):
                cell_text = row[j] if j < len(row) else ""
                self.pdf.cell(col_w, 7, cell_text, border=1, fill=True)
            self.pdf.ln()

        self.pdf.set_text_color(0, 0, 0)
        self.pdf.ln(3)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate PDF from HTML")
    parser.add_argument("--input", required=True, help="Input HTML file path")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument(
        "--skill-name", required=True,
        help="Skill name for output filename",
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    html_content = input_path.read_text(encoding="utf-8")
    base_dir = str(input_path.parent)

    # Resolve fonts
    os_name = platform.system()
    font_result = _find_font(_FONT_CANDIDATES.get(os_name, []))
    mono_result = _find_font(_MONO_CANDIDATES.get(os_name, []))

    if not font_result:
        print(
            f"Error: No Japanese font found for {os_name}. "
            "Install Noto Sans JP or ensure system Japanese fonts are available.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not mono_result:
        # Fall back to the same Japanese font for mono
        mono_result = font_result

    pdf = PDFDocument(font_result[0], font_result[1], mono_result[0], mono_result[1])
    pdf.set_title(args.skill_name)

    parser_inst = HTMLToPDFParser(pdf, base_dir)
    parser_inst.feed(html_content)
    parser_inst._flush_text()

    output_path = output_dir / f"{args.skill_name}.pdf"
    pdf.output(str(output_path))
    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    main()
