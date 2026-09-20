"""
Generate 申論題全科攻略.pdf — full 6-subject essay guide.
Reuses the parser from _make_pdf2.py with tweaked styles.
"""
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, PageBreak)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont('Kaiu',   r'C:\Windows\Fonts\kaiu.ttf'))
pdfmetrics.registerFont(TTFont('MsjhBd', r'C:\Windows\Fonts\msjhbd.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('Msjh',   r'C:\Windows\Fonts\msjh.ttc',   subfontIndex=0))

PAGE_W, PAGE_H = A4
ML = 18 * mm

C = {
    'dark':   colors.HexColor('#0d1b2a'),
    'blue':   colors.HexColor('#1b4332'),
    'accent': colors.HexColor('#2d6a4f'),
    'purple': colors.HexColor('#40916c'),
    'bgblue': colors.HexColor('#d8f3dc'),
    'bggrn':  colors.HexColor('#e8f5e9'),
    'bggry':  colors.HexColor('#f8f9fa'),
    'line':   colors.HexColor('#ced4da'),
    'red':    colors.HexColor('#c62828'),
    'orange': colors.HexColor('#e65100'),
}

B = dict(fontName='Kaiu', wordWrap='CJK')

SUBJ_COLORS = {
    '保險學概要':     '#1565c0',
    '保險法規概要':   '#6a1b9a',
    '人身保險行銷':   '#00695c',
    '財產保險行銷':   '#e65100',
    '人身風險管理':   '#283593',
    '財產風險管理':   '#4e342e',
}

def subject_color(heading):
    for k, v in SUBJ_COLORS.items():
        if k in heading:
            return colors.HexColor(v)
    return colors.HexColor('#1a1a2e')

def make_h2_style(bg):
    return ParagraphStyle('h2x', fontName='MsjhBd', fontSize=14, leading=21,
                           spaceBefore=14, spaceAfter=5,
                           textColor=colors.white, backColor=bg, borderPad=6)

styles = {
    'h1':  ParagraphStyle('h1',  fontName='MsjhBd', fontSize=18, leading=26,
                           spaceAfter=6, textColor=C['dark']),
    'h3':  ParagraphStyle('h3',  fontName='MsjhBd', fontSize=11.5, leading=17,
                           spaceBefore=10, spaceAfter=3,
                           textColor=C['accent'],
                           backColor=C['bgblue'], borderPad=4),
    'h4':  ParagraphStyle('h4',  fontName='MsjhBd', fontSize=10.5, leading=16,
                           spaceBefore=8, spaceAfter=2,
                           textColor=C['red']),
    'body':ParagraphStyle('body', **B, fontSize=10, leading=17, spaceAfter=3),
    'bul': ParagraphStyle('bul',  **B, fontSize=10, leading=16,
                           leftIndent=14, spaceAfter=2),
    'bul2':ParagraphStyle('bul2', **B, fontSize=9.5, leading=15,
                           leftIndent=28, spaceAfter=2),
    'code':ParagraphStyle('code', fontName='Kaiu', fontSize=9.5, leading=16,
                           leftIndent=8, backColor=C['bggry'],
                           borderWidth=2, borderColor=C['accent'],
                           borderPad=7, spaceAfter=7, wordWrap='CJK'),
    'tip': ParagraphStyle('tip',  **B, fontSize=9.5, leading=15,
                           leftIndent=10, backColor=colors.HexColor('#fff3e0'),
                           borderWidth=3, borderColor=C['orange'],
                           borderPad=5, spaceAfter=5),
    'th':  ParagraphStyle('th', fontName='MsjhBd', fontSize=9, leading=13,
                           wordWrap='CJK', textColor=colors.white),
    'td':  ParagraphStyle('td', fontName='Kaiu', fontSize=9, leading=13,
                           wordWrap='CJK'),
}

def esc(t):
    return t.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def fmt(t):
    t = esc(t.strip())
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'\*(.+?)\*',     r'<i>\1</i>', t)
    t = re.sub(r'`(.+?)`',
               r'<font face="Kaiu" size="9" color="#c62828">\1</font>', t)
    return t

def build_table(rows_raw):
    rows = []
    for line in rows_raw:
        line = line.strip().strip('|')
        if re.match(r'^[-| :]+$', line):
            continue
        cells = [c.strip() for c in line.split('|')]
        rows.append(cells)
    if not rows:
        return Spacer(1, 1)
    nc = max(len(r) for r in rows)
    rows = [r + [''] * (nc - len(r)) for r in rows]

    # Detect header row for colour
    data = []
    for ri, row in enumerate(rows):
        st = styles['th'] if ri == 0 else styles['td']
        data.append([Paragraph(fmt(c), st) for c in row])

    avail = PAGE_W - 2 * ML
    cw = avail / nc
    t = Table(data, colWidths=[cw] * nc, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  colors.HexColor('#1b4332')),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [C['bggry'], colors.white]),
        ('GRID',          (0,0), (-1,-1), 0.3, C['line']),
        ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING',   (0,0), (-1,-1), 5),
        ('RIGHTPADDING',  (0,0), (-1,-1), 5),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    return t

def build_code(lines):
    text = '<br/>'.join(esc(l) for l in lines)
    return Paragraph(text, styles['code'])

_current_h2_color = [colors.HexColor('#1a1a2e')]

def parse(md):
    flowables = []
    lines = md.split('\n')
    i = 0
    tbl_buf = []
    code_buf = []
    in_code = False

    while i < len(lines):
        raw = lines[i]
        s = raw.strip()

        if s.startswith('```'):
            if not in_code:
                in_code = True; code_buf = []
            else:
                if code_buf:
                    flowables.append(build_code(code_buf))
                in_code = False
            i += 1; continue
        if in_code:
            code_buf.append(raw); i += 1; continue

        if tbl_buf and not (s.startswith('|') or re.match(r'^[-| :]+$', s)):
            flowables.append(build_table(tbl_buf))
            flowables.append(Spacer(1, 4))
            tbl_buf = []

        if s.startswith('|'):
            tbl_buf.append(s); i += 1; continue

        if re.match(r'^---+$', s):
            flowables.append(HRFlowable(width='100%', thickness=0.5,
                                        color=C['line'], spaceAfter=4))
            i += 1; continue

        if s.startswith('> '):
            flowables.append(Paragraph(fmt(s[2:]), styles['tip']))
            i += 1; continue

        if s.startswith('# ') and not s.startswith('##'):
            if flowables:
                flowables.append(PageBreak())
            flowables.append(Paragraph(fmt(s[2:]), styles['h1']))
            i += 1; continue

        if s.startswith('## '):
            heading = s[3:]
            col = subject_color(heading)
            _current_h2_color[0] = col
            h2s = make_h2_style(col)
            flowables.append(Paragraph('  ' + fmt(heading), h2s))
            i += 1; continue

        if s.startswith('### '):
            flowables.append(Paragraph(fmt(s[4:]), styles['h3']))
            i += 1; continue

        if s.startswith('#### '):
            flowables.append(Paragraph(fmt(s[5:]), styles['h4']))
            i += 1; continue

        m = re.match(r'^([-*]|\d+\.) (.+)', s)
        if m:
            flowables.append(Paragraph('• ' + fmt(m.group(2)), styles['bul']))
            i += 1; continue

        m2 = re.match(r'^ {2,4}[-*] (.+)', raw)
        if m2:
            flowables.append(Paragraph('◦ ' + fmt(m2.group(1)), styles['bul2']))
            i += 1; continue

        if not s:
            flowables.append(Spacer(1, 4)); i += 1; continue

        flowables.append(Paragraph(fmt(s), styles['body']))
        i += 1

    if tbl_buf:
        flowables.append(build_table(tbl_buf))
    if code_buf:
        flowables.append(build_code(code_buf))
    return flowables


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Kaiu', 8.5)
    canvas.setFillColor(colors.HexColor('#888888'))
    canvas.drawCentredString(PAGE_W / 2, 12 * mm,
        f'保險經紀人資格考試 申論題全科攻略（人身＋財產）  第 {doc.page} 頁')
    canvas.restoreState()


MD  = r'C:\Users\david\insurance-exam\申論題全科攻略.md'
OUT = r'C:\Users\david\insurance-exam\申論題全科攻略.pdf'

with open(MD, 'r', encoding='utf-8') as f:
    md = f.read()

doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    leftMargin=ML, rightMargin=ML,
    topMargin=20*mm, bottomMargin=22*mm,
    title='保險經紀人 申論題全科攻略',
)
doc.build(parse(md), onFirstPage=footer, onLaterPages=footer)
print(f'Done → {OUT}')
