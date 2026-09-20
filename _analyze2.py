import json, re, unicodedata, sys
from collections import defaultdict

sys.stdout = open(r'C:\Users\david\insurance-exam\_report.txt', 'w', encoding='utf-8')

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
print()

# Show all dup groups
print('--- All duplicate groups ---')
sorted_dups = sorted(dup_groups.items(), key=lambda x: -len(x[1]))
for key, idxs in sorted_dups:
    years = [qs[i]['year'] for i in idxs]
    answers = [qs[i]['answer'] for i in idxs]
    sections = list(set(qs[i]['section'] for i in idxs))
    print(f'[{len(idxs)} copies] years={years} answers={answers}')
    print(f'  sections={sections}')
    print(f'  Q: {qs[idxs[0]]["question"][:80]}')
    print()

# Count by section
print('--- Section distribution ---')
secs = defaultdict(int)
for q in qs:
    secs[q['section']] += 1
for sec, cnt in sorted(secs.items(), key=lambda x: -x[1]):
    print(f'  {sec}: {cnt}')

print()

# Year distribution
print('--- Year distribution ---')
years = defaultdict(int)
for q in qs:
    years[q['year']] += 1
for yr, cnt in sorted(years.items()):
    print(f'  {yr}: {cnt}')

sys.stdout.close()
print('Done - see _report.txt', file=sys.stderr)
