"""
Convert 申論題整理與猜題.md to PDF using reportlab with Traditional Chinese font.
"""
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, PageBreak)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Traditional Chinese font
FONT_PATH = r'C:\Windows\Fonts\kaiu.ttf'
BOLD_PATH = r'C:\Windows\Fonts\msjhbd.ttc'   # 微軟正黑體 Bold

pdfmetrics.registerFont(TTFont('Kaiu', FONT_PATH))
pdfmetrics.registerFont(TTFont('MsjhBd', BOLD_PATH, subfontIndex=0))

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm

# ─── Styles ────────────────────────────────────────────────────────────
base = dict(fontName='Kaiu', fontSize=10, leading=17, wordWrap='CJK')

styles = {
    'h1': ParagraphStyle('h1', fontName='MsjhBd', fontSize=18, leading=26,
                         spaceAfter=6, textColor=colors.HexColor('#1a1a2e')),
    'h2': ParagraphStyle('h2', fontName='MsjhBd', fontSize=14, leading=20,
                         spaceBefore=12, spaceAfter=4,
                         textColor=colors.HexColor('#16213e'),
                         borderPad=3, borderWidth=0,
                         backColor=colors.HexColor('#e8eaf6'),
                         borderRadius=3),
    'h3': ParagraphStyle('h3', fontName='MsjhBd', fontSize=12, leading=18,
                         spaceBefore=10, spaceAfter=3,
                         textColor=colors.HexColor('#0f3460')),
    'h4': ParagraphStyle('h4', fontName='MsjhBd', fontSize=10.5, leading=16,
                         spaceBefore=8, spaceAfter=2,
                         textColor=colors.HexColor('#533483')),
    'body': ParagraphStyle('body', **base, spaceAfter=4),
    'bullet': ParagraphStyle('bullet', **base, leftIndent=12, spaceAfter=3,
                              bulletIndent=4),
    'bullet2': ParagraphStyle('bullet2', **base, leftIndent=24, spaceAfter=2,
                               bulletIndent=16),
    'quote': ParagraphStyle('quote', **base, leftIndent=10,
                             backColor=colors.HexColor('#f5f5f5'),
                             borderWidth=2, borderColor=colors.HexColor('#1976d2'),
                             borderPad=6, spaceAfter=6),
    'answer': ParagraphStyle('answer', **base, leftIndent=10,
                              backColor=colors.HexColor('#e8f5e9'),
                              borderPad=5, spaceAfter=4),
    'table_h': ParagraphStyle('table_h', fontName='MsjhBd', fontSize=9,
                               leading=13, wordWrap='CJK',
                               textColor=colors.white),
    'table_b': ParagraphStyle('table_b', fontName='Kaiu', fontSize=9,
                               leading=13, wordWrap='CJK'),
}

def esc(text):
    """Escape XML special chars for ReportLab."""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;'))

def make_bold(text):
    """Replace **text** with bold tags."""
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', esc(text))

def parse_md(md_text):
    """Parse markdown into ReportLab flowables."""
    flowables = []
    lines = md_text.split('\n')
    i = 0

    def add_para(text, style):
        text = make_bold(text.strip())
        if text:
            flowables.append(Paragraph(text, styles[style]))

    # Table buffer
    table_lines = []
    in_table = False

    while i < len(lines):
        line = lines[i]

        # ── Table detection ──
        if '|' in line and line.strip().startswith('|'):
            table_lines.append(line)
            i += 1
            continue
        else:
            if table_lines:
                flowables.append(build_table(table_lines))
                flowables.append(Spacer(1, 4))
                table_lines = []

        stripped = line.strip()

        # Skip separator lines and HTML comments
        if re.match(r'^---+$', stripped) or stripped.startswith('> 資料來源'):
            if re.match(r'^---+$', stripped):
                flowables.append(HRFlowable(width='100%', thickness=0.5,
                                            color=colors.HexColor('#cccccc'),
                                            spaceAfter=4))
            i += 1
            continue

        if stripped.startswith('# '):
            add_para(stripped[2:], 'h1')
        elif stripped.startswith('## '):
            add_para('　' + stripped[3:], 'h2')
        elif stripped.startswith('### '):
            add_para(stripped[4:], 'h3')
        elif stripped.startswith('#### '):
            add_para(stripped[5:], 'h4')
        elif stripped.startswith('> '):
            add_para(stripped[2:], 'quote')
        elif re.match(r'^[-*] ', stripped):
            txt = stripped[2:]
            # Check if it's an answer line (indented sub-bullet content)
            add_para('• ' + txt, 'bullet')
        elif re.match(r'^  [-*] ', stripped):
            txt = stripped[4:]
            add_para('◦ ' + txt, 'bullet2')
        elif re.match(r'^\d+\. ', stripped):
            m = re.match(r'^(\d+)\. (.+)', stripped)
            if m:
                add_para(f'{m.group(1)}. {m.group(2)}', 'bullet')
        elif stripped == '':
            flowables.append(Spacer(1, 4))
        else:
            add_para(stripped, 'body')

        i += 1

    if table_lines:
        flowables.append(build_table(table_lines))

    return flowables


def build_table(table_lines):
    """Build a ReportLab Table from markdown table lines."""
    rows = []
    is_header = True
    sep_seen = False

    for line in table_lines:
        line = line.strip()
        if not line or line.startswith('|--') or re.match(r'^\|[-| :]+\|$', line):
            sep_seen = True
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        rows.append(cells)

    if not rows:
        return Spacer(1, 1)

    col_count = max(len(r) for r in rows)
    # Normalize row lengths
    rows = [r + [''] * (col_count - len(r)) for r in rows]

    # Convert cells to Paragraphs
    table_data = []
    for ri, row in enumerate(rows):
        style = styles['table_h'] if ri == 0 else styles['table_b']
        table_data.append([Paragraph(make_bold(esc(c)), style) for c in row])

    avail = PAGE_W - 2 * MARGIN
    col_w = avail / col_count

    t = Table(table_data, colWidths=[col_w] * col_count, repeatRows=1)
    ts = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'MsjhBd'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.HexColor('#f9f9f9'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#cccccc')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ])
    t.setStyle(ts)
    return t


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont('Kaiu', 9)
    canvas.setFillColor(colors.HexColor('#888888'))
    canvas.drawCentredString(PAGE_W / 2, 12 * mm,
                             f'保險經紀人法規概要 申論題整理  第 {doc.page} 頁')
    canvas.restoreState()


# ─── Main ──────────────────────────────────────────────────────────────
MD_FILE = r'C:\Users\david\insurance-exam\申論題整理與猜題.md'
PDF_FILE = r'C:\Users\david\insurance-exam\申論題整理與猜題.pdf'

with open(MD_FILE, 'r', encoding='utf-8') as f:
    md_content = f.read()

doc = SimpleDocTemplate(
    PDF_FILE, pagesize=A4,
    leftMargin=MARGIN, rightMargin=MARGIN,
    topMargin=MARGIN, bottomMargin=22 * mm,
    title='保險經紀人法規概要 申論題整理與猜題',
    author='insurance-exam'
)

story = parse_md(md_content)
doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
print(f'PDF saved: {PDF_FILE}')
