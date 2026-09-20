import json, re, unicodedata
from collections import defaultdict

def normalize(s):
    s = unicodedata.normalize('NFKC', s)
    s = re.sub(r'\s+', '', s)
    s = re.sub(r'[，。？！、：；「」『』（）【】〔〕…—\-_]', '', s)
    return s.lower()

with open(r'C:\Users\david\insurance-exam\questions.json', 'r', encoding='utf-8') as f:
    qs = json.load(f)

print(f'Total questions: {len(qs)}')

# Group by normalized question text
groups = defaultdict(list)
for i, q in enumerate(qs):
    key = normalize(q['question'])
    groups[key].append(i)

dup_groups = {k: v for k, v in groups.items() if len(v) > 1}
total_dups = sum(len(v) - 1 for v in dup_groups.values())
print(f'Duplicate groups: {len(dup_groups)}')
print(f'Extra duplicate questions to remove: {total_dups}')

# Show top 10 dup groups
print('\n--- Top 10 duplicate groups ---')
sorted_dups = sorted(dup_groups.items(), key=lambda x: -len(x[1]))
for key, idxs in sorted_dups[:10]:
    print(f'  [{len(idxs)} copies] years={[qs[i]["year"] for i in idxs]} sections={list(set(qs[i]["section"] for i in idxs))}')
    print(f'    Q: {qs[idxs[0]]["question"][:60]}...')

# Count by section
print('\n--- Section distribution ---')
secs = defaultdict(int)
for q in qs:
    secs[q['section']] += 1
for sec, cnt in sorted(secs.items(), key=lambda x: -x[1]):
    print(f'  {sec}: {cnt}')
