import json, re, unicodedata, sys
from collections import defaultdict

sys.stdout = open(r'C:\Users\david\insurance-exam\_report2.txt', 'w', encoding='utf-8')

def normalize(s):
    s = unicodedata.normalize('NFKC', s)
    s = re.sub(r'\s+', '', s)
    s = re.sub(r'[，。？！、：；「」『』（）【】〔〕…—\-_①②③④⑤⑥⑦⑧⑨⑩]', '', s)
    return s.lower()

def full_key(q):
    text = q['question'] + '|' + '|'.join(q['options'].get(k,'') for k in 'ABCD')
    return normalize(text)

with open(r'C:\Users\david\insurance-exam\questions.json', 'r', encoding='utf-8') as f:
    qs = json.load(f)

print(f'Total questions: {len(qs)}')

# True duplicates: same question + same options
full_groups = defaultdict(list)
for i, q in enumerate(qs):
    key = full_key(q)
    full_groups[key].append(i)

true_dups = {k: v for k, v in full_groups.items() if len(v) > 1}
true_dup_count = sum(len(v)-1 for v in true_dups.values())
print(f'True duplicate groups (same Q+options): {len(true_dups)}')
print(f'True duplicates to remove: {true_dup_count}')
print()

print('=== TRUE DUPLICATES ===')
for key, idxs in sorted(true_dups.items(), key=lambda x: -len(x[1])):
    print(f'[{len(idxs)} copies] years={[qs[i]["year"] for i in idxs]} sections={[qs[i]["section"] for i in idxs]}')
    print(f'  answers={[qs[i]["answer"] for i in idxs]}')
    print(f'  Q: {qs[idxs[0]]["question"][:100]}')
    print()

# Now check for conflicting answers (same Q+options but different answers)
same_q_diff_ans = defaultdict(list)
for i, q in enumerate(qs):
    key = normalize(q['question'] + '|' + '|'.join(q['options'].get(k,'') for k in 'ABCD'))
    same_q_diff_ans[key].append(i)

conflicts = []
for key, idxs in same_q_diff_ans.items():
    if len(idxs) > 1:
        answers = set(qs[i]['answer'] for i in idxs)
        if len(answers) > 1:
            conflicts.append((key, idxs))

print(f'=== CONFLICTING ANSWERS (same Q, different answers) ===')
print(f'Count: {len(conflicts)}')
for key, idxs in conflicts[:20]:
    print(f'years={[qs[i]["year"] for i in idxs]} answers={[qs[i]["answer"] for i in idxs]}')
    print(f'  Q: {qs[idxs[0]]["question"][:80]}')
    for k in 'ABCD':
        print(f'  {k}: {qs[idxs[0]]["options"].get(k,"")}')
    print()

# Now look at law section questions - search for potentially outdated content
print('=== 保險法規概要 section analysis ===')
law_qs = [q for q in qs if '保險法規概要' in q.get('section','') and '現行法令' not in q.get('section','')]
print(f'保險法規概要 questions: {len(law_qs)}')

# Year distribution for law section
law_years = defaultdict(int)
for q in law_qs:
    law_years[q['year']] += 1
print('Year distribution:')
for yr, cnt in sorted(law_years.items()):
    print(f'  {yr}: {cnt}')

# Look for potentially outdated number references
print()
print('=== Questions with specific numbers/values (potential outdated provisions) ===')
# Known current values:
# - 遲延利息: 年利一分 (1%)
# - 事故通知: 5日
# - 複保險通知義務存在
# - 停效: 30日
# - 復效: 6個月 / 2年
# - 保單借款: 1年

outdated_patterns = [
    ('年利二分', '遲延利息舊規定(應為一分)'),
    ('年利三分', '遲延利息舊規定(應為一分)'),
    ('三日內通知', '通知期限舊規定(應為5日)'),
    ('十日內通知', '通知期限可能過時'),
    ('三個月', '停效期間可能過時'),
    ('六十日', '可能過時條文'),
]

for pattern, desc in outdated_patterns:
    matched = [(i, q) for i, q in enumerate(qs) if pattern in q['question'] or any(pattern in v for v in q['options'].values())]
    if matched:
        print(f'\n[{desc}] - {len(matched)} questions')
        for i, q in matched[:3]:
            print(f'  year={q["year"]} section={q["section"]}')
            print(f'  Q: {q["question"][:80]}')
            print(f'  answer={q["answer"]}')

sys.stdout.close()
print('Done', file=sys.stderr)
