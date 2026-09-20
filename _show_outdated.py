import json, re, sys
sys.stdout = open(r'C:\Users\david\insurance-exam\_outdated.txt', 'w', encoding='utf-8')

with open(r'C:\Users\david\insurance-exam\questions.json', 'r', encoding='utf-8') as f:
    qs = json.load(f)

def show(i):
    q = qs[i]
    print(f'[{i}] year={q["year"]} section={q["section"]} ans={q["answer"]}')
    print(f'  Q: {q["question"][:200]}')
    for k in 'ABCD':
        v = q['options'].get(k,'')
        mark = ' <<<<' if k == q['answer'] else ''
        print(f'  {k}: {v}{mark}')
    print()

# All questions referencing specific amendment dates
old_patterns = [
    r'\d{2,3}\s*年\s*\d+\s*月\s*\d+\s*日\s*修正',
    r'依\s*\d{2,3}\s*年\s*修正',
]

print('=== 引用特定修正日期的題目 ===')
for i, q in enumerate(qs):
    text = q['question'] + ' ' + ' '.join(q['options'].values())
    for pat in old_patterns:
        if re.search(pat, text):
            show(i)
            break

# True duplicate indices
print('=== 能量釋放理論重複題 ===')
for i, q in enumerate(qs):
    if '能量釋放理論' in q['question']:
        show(i)

sys.stdout.close()
print('Done', file=sys.stderr)
