import json, re, unicodedata, sys

with open(r'C:\Users\david\insurance-exam\questions.json', 'r', encoding='utf-8') as f:
    qs = json.load(f)

def normalize(s):
    s = unicodedata.normalize('NFKC', s)
    s = re.sub(r'\s+', '', s)
    s = re.sub(r'[，。？！、：；「」『』（）【】〔〕…—\-_①②③④⑤⑥⑦⑧⑨⑩]', '', s)
    return s.lower()

target = '根據能量釋放理論'
for i, q in enumerate(qs):
    if target in q['question']:
        print(f'[{i}] year={q["year"]} section={q["section"]} ans={q["answer"]}')
        print(f'  Q: {q["question"][:80]}')

# Also search for any other old-amendment references
print('\n--- 引用舊修正版本的題目 ---')
old_patterns = [
    r'\d{2,3}\s*年\s*\d+\s*月\s*\d+\s*日\s*修正',
    r'依\s*\d{2,3}\s*年\s*修正',
]
for i, q in enumerate(qs):
    text = q['question'] + ' ' + ' '.join(q['options'].values())
    for pat in old_patterns:
        if re.search(pat, text):
            print(f'[{i}] year={q["year"]} section={q["section"]}')
            print(f'  Q: {q["question"][:100]}')
            break
