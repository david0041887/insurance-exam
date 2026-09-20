import json, sys

with open(r'C:\Users\david\insurance-exam\questions.json', 'r', encoding='utf-8') as f:
    qs = json.load(f)

print(f'原始題目數: {len(qs)}', file=sys.stderr)

# Indices to remove (0-based)
# [2490] true duplicate of [3054] (energy release theory)
# [804][805][822] explicitly test 104年2月4日修正保險法 (superseded)
# [269][310] explicitly test 110年3月3日修正之保險經紀人管理規則 (superseded by 111年)
# [38] explicitly tests pre-111年9月22日 rules ("修正施行前之")
REMOVE = {2490, 804, 805, 822, 269, 310, 38}

# Show what we're removing
for i in sorted(REMOVE):
    q = qs[i]
    print(f'  刪除[{i}] year={q["year"]} ans={q["answer"]} Q: {q["question"][:60]}', file=sys.stderr)

filtered = [q for i, q in enumerate(qs) if i not in REMOVE]
print(f'過濾後題目數: {len(filtered)} (刪除 {len(qs)-len(filtered)} 題)', file=sys.stderr)

with open(r'C:\Users\david\insurance-exam\questions.json', 'w', encoding='utf-8') as f:
    json.dump(filtered, f, ensure_ascii=False, separators=(',', ':'))

print('Done', file=sys.stderr)
