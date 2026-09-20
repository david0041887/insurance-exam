"""
Generate 六科精準整理與猜題.pdf from markdown with full Traditional Chinese support.
"""
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, PageBreak, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ─── Fonts ────────────────────────────────────────────────────────────
pdfmetrics.registerFont(TTFont('Kaiu',   r'C:\Windows\Fonts\kaiu.ttf'))
pdfmetrics.registerFont(TTFont('MsjhBd', r'C:\Windows\Fonts\msjhbd.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('Msjh',   r'C:\Windows\Fonts\msjh.ttc',   subfontIndex=0))

PAGE_W, PAGE_H = A4
MARGIN_LR = 18 * mm
MARGIN_TB = 20 * mm

# ─── Colour palette ───────────────────────────────────────────────────
C_DARK   = colors.HexColor('#1a1a2e')
C_BLUE   = colors.HexColor('#16213e')
C_ACCENT = colors.HexColor('#0f3460')
C_PURPLE = colors.HexColor('#533483')
C_GREEN  = colors.HexColor('#1b5e20')
C_BGBLUE = colors.HexColor('#e8eaf6')
C_BGGRN  = colors.HexColor('#e8f5e9')
C_BGGRY  = colors.HexColor('#f5f5f5')
C_THEAD  = colors.HexColor('#1a1a2e')
C_LINE   = colors.HexColor('#cccccc')

B = dict(fontName='Kaiu', wordWrap='CJK')

styles = {
    'h1':     ParagraphStyle('h1',  fontName='MsjhBd', fontSize=20, leading=28,
                              spaceAfter=8, textColor=C_DARK),
    'h2':     ParagraphStyle('h2',  fontName='MsjhBd', fontSize=15, leading=22,
                              spaceBefore=14, spaceAfter=5, textColor=colors.white,
                              backColor=C_DARK, borderPad=5),
    'h3':     ParagraphStyle('h3',  fontName='MsjhBd', fontSize=12, leading=18,
                              spaceBefore=10, spaceAfter=3, textColor=C_ACCENT,
                              backColor=C_BGBLUE, borderPad=4),
    'h4':     ParagraphStyle('h4',  fontName='MsjhBd', fontSize=10.5, leading=16,
                              spaceBefore=8, spaceAfter=2, textColor=C_PURPLE),
    'body':   ParagraphStyle('body', **B, fontSize=10, leading=17, spaceAfter=3),
    'bullet': ParagraphStyle('bullet', **B, fontSize=10, leading=16,
                              leftIndent=14, spaceAfter=2),
    'bullet2':ParagraphStyle('bullet2', **B, fontSize=9.5, leading=15,
                              leftIndent=28, spaceAfter=2),
    'code':   ParagraphStyle('code', fontName='Kaiu', fontSize=9, leading=15,
                              leftIndent=8, backColor=C_BGGRY, borderPad=6,
                              spaceAfter=6, wordWrap='CJK'),
    'quote':  ParagraphStyle('quote', **B, fontSize=9.5, leading=15,
                              leftIndent=10, backColor=C_BGGRY,
                              borderWidth=3, borderColor=C_ACCENT,
                              borderPad=5, spaceAfter=5),
    'th':     ParagraphStyle('th', fontName='MsjhBd', fontSize=9, leading=13,
                              wordWrap='CJK', textColor=colors.white),
    'td':     ParagraphStyle('td', fontName='Kaiu',   fontSize=9, leading=13,
                              wordWrap='CJK'),
    'footer': ParagraphStyle('footer', fontName='Kaiu', fontSize=8.5,
                              textColor=colors.HexColor('#888888')),
}

# ─── helpers ──────────────────────────────────────────────────────────
def esc(t):
    return t.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def fmt(t):
    t = esc(t.strip())
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'\*(.+?)\*',     r'<i>\1</i>', t)
    t = re.sub(r'`(.+?)`',       r'<font face="Kaiu" size="9">\1</font>', t)
    return t

# ─── table builder ────────────────────────────────────────────────────
def build_table(rows_raw):
    rows = []
    for line in rows_raw:
        line = line.strip().strip('|')
        if re.match(r'^[-| :]+$', line):
            continue
        cells = [c.strip() for c in line.split('|')]
        rows.append(cells)
    if not rows:
        return Spacer(1,1)
    ncols = max(len(r) for r in rows)
    rows = [r + ['']*(ncols-len(r)) for r in rows]

    data = []
    for ri, row in enumerate(rows):
        st = styles['th'] if ri == 0 else styles['td']
        data.append([Paragraph(fmt(c), st) for c in row])

    avail = PAGE_W - 2*MARGIN_LR
    col_w = avail / ncols

    t = Table(data, colWidths=[col_w]*ncols, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,0),  C_THEAD),
        ('TEXTCOLOR',    (0,0), (-1,0),  colors.white),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [C_BGGRY, colors.white]),
        ('GRID',         (0,0), (-1,-1), 0.3, C_LINE),
        ('VALIGN',       (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING',  (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING',   (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0), (-1,-1), 4),
    ]))
    return t

# ─── code block builder ───────────────────────────────────────────────
def build_code(lines):
    text = '\n'.join(esc(l) for l in lines)
    return Paragraph(text.replace('\n','<br/>'), styles['code'])

# ─── main parser ──────────────────────────────────────────────────────
def parse(md):
    flowables = []
    lines = md.split('\n')
    i = 0
    table_buf = []
    code_buf  = []
    in_code   = False

    while i < len(lines):
        raw = lines[i]
        s   = raw.strip()

        # code fence
        if s.startswith('```'):
            if not in_code:
                in_code = True
                code_buf = []
            else:
                if code_buf:
                    flowables.append(build_code(code_buf))
                in_code = False
            i += 1
            continue
        if in_code:
            code_buf.append(raw)
            i += 1
            continue

        # flush table if next line is not table
        if table_buf and not (s.startswith('|') or re.match(r'^[-| :]+$', s)):
            flowables.append(build_table(table_buf))
            flowables.append(Spacer(1,4))
            table_buf = []

        # table line
        if s.startswith('|'):
            table_buf.append(s)
            i += 1
            continue

        # separators / hr
        if re.match(r'^---+$', s):
            flowables.append(HRFlowable(width='100%', thickness=0.5,
                                        color=C_LINE, spaceAfter=4))
            i += 1
            continue

        # blockquote (> 資料來源…)
        if s.startswith('> '):
            flowables.append(Paragraph(fmt(s[2:]), styles['quote']))
            i += 1
            continue

        # headings
        if s.startswith('# ') and not s.startswith('##'):
            # Page break before each top-level section (except first)
            if flowables:
                flowables.append(PageBreak())
            flowables.append(Paragraph(fmt(s[2:]), styles['h1']))
            i += 1
            continue
        if s.startswith('## '):
            flowables.append(Paragraph('  ' + fmt(s[3:]), styles['h2']))
            i += 1
            continue
        if s.startswith('### '):
            flowables.append(Paragraph(fmt(s[4:]), styles['h3']))
            i += 1
            continue
        if s.startswith('#### '):
            flowables.append(Paragraph(fmt(s[5:]), styles['h4']))
            i += 1
            continue

        # bullets
        m = re.match(r'^([-*]|\d+\.) (.+)', s)
        if m:
            txt = m.group(2)
            flowables.append(Paragraph('• ' + fmt(txt), styles['bullet']))
            i += 1
            continue
        m2 = re.match(r'^ {2,4}([-*]) (.+)', raw)
        if m2:
            flowables.append(Paragraph('◦ ' + fmt(m2.group(2)), styles['bullet2']))
            i += 1
            continue

        # empty line
        if not s:
            flowables.append(Spacer(1, 4))
            i += 1
            continue

        # normal paragraph
        flowables.append(Paragraph(fmt(s), styles['body']))
        i += 1

    if table_buf:
        flowables.append(build_table(table_buf))
    if code_buf:
        flowables.append(build_code(code_buf))

    return flowables


# ─── footer ───────────────────────────────────────────────────────────
def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Kaiu', 8.5)
    canvas.setFillColor(colors.HexColor('#888888'))
    canvas.drawCentredString(PAGE_W/2, 12*mm,
        f'保險經紀人資格考試 六科精準整理與猜題  第 {doc.page} 頁')
    canvas.restoreState()


# ─── run ──────────────────────────────────────────────────────────────
MD  = r'C:\Users\david\insurance-exam\六科精準整理與猜題.md'
OUT = r'C:\Users\david\insurance-exam\六科精準整理與猜題.pdf'

with open(MD, 'r', encoding='utf-8') as f:
    md = f.read()

doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    leftMargin=MARGIN_LR, rightMargin=MARGIN_LR,
    topMargin=MARGIN_TB,  bottomMargin=22*mm,
    title='保險經紀人資格考試 六科精準整理與猜題',
)
story = parse(md)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(f'Done → {OUT}')
