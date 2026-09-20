import json, re, sys
from collections import defaultdict

sys.stdout = open(r'C:\Users\david\insurance-exam\_law_report.txt', 'w', encoding='utf-8')

with open(r'C:\Users\david\insurance-exam\questions.json', 'r', encoding='utf-8') as f:
    qs = json.load(f)

law_qs = [(i, q) for i, q in enumerate(qs) if '保險法規概要' in q.get('section','') and '現行法令' not in q.get('section','')]
print(f'保險法規概要 questions: {len(law_qs)}')

# ---------- 篩選已知過時條文 ----------
OUTDATED_IDS = set()

# 1. 明確引用特定舊版修正年份
old_ref_patterns = [
    r'依\d{2,3}年\d+月\d*日修正',
    r'依\d{2,3}年修正之保險法',
    r'\d{2,3}年\d+月\d+日修正',
]
print('\n=== 引用特定舊修正版本 ===')
for i, q in law_qs:
    text = q['question'] + ' ' + ' '.join(q['options'].values())
    for pat in old_ref_patterns:
        m = re.search(pat, text)
        if m:
            OUTDATED_IDS.add(i)
            print(f'[{i}] year={q["year"]} | {q["question"][:80]}')
            print(f'     match: {m.group()}')
            break

# 2. 業務員登錄有效期間錯誤（現行規定：5年，舊規定有些題說4年/無期限等）
print('\n=== 業務員登錄期間 ===')
period_qs = [(i,q) for i,q in law_qs if '登錄' in q['question'] and ('有效' in q['question'] or '期間' in q['question'])]
for i, q in period_qs[:10]:
    print(f'[{i}] year={q["year"]} ans={q["answer"]}')
    print(f'  Q: {q["question"][:80]}')
    for k in 'ABCD':
        print(f'  {k}: {q["options"].get(k,"")}')
    print()

# 3. 保費通知期限 (現行5日) — 舊規定曾是3日
print('\n=== 保費通知期限相關 ===')
notify_qs = [(i,q) for i,q in law_qs if ('通知' in q['question'] or '通知' in ' '.join(q['options'].values())) and ('日' in q['question'] or '日' in ' '.join(q['options'].values()))]
# Show ones mentioning specific days
for i, q in notify_qs[:5]:
    if any(x in q['question'] for x in ['三日', '五日', '七日', '十日', '15日', '3日', '5日', '7日']):
        print(f'[{i}] year={q["year"]} ans={q["answer"]}')
        print(f'  Q: {q["question"][:80]}')
        for k in 'ABCD':
            print(f'  {k}: {q["options"].get(k,"")}')
        print()

# 4. 明確測試遲延利息金額
print('\n=== 遲延利息題目 (年利X分) ===')
delay_qs = [(i,q) for i,q in law_qs if '遲延' in q['question'] and '利息' in q['question']]
for i, q in delay_qs[:5]:
    print(f'[{i}] year={q["year"]} ans={q["answer"]}')
    print(f'  Q: {q["question"][:80]}')
    for k in 'ABCD':
        print(f'  {k}: {q["options"].get(k,"")}')
    print()

# 5. 保費停效/復效條件 (現行: 催告30日停效, 6個月/2年復效)
print('\n=== 停效/復效相關 ===')
eff_qs = [(i,q) for i,q in law_qs if ('停止效力' in q['question'] or '停效' in q['question'] or '恢復效力' in q['question'] or '復效' in q['question'])]
print(f'找到 {len(eff_qs)} 題')
for i, q in eff_qs[:8]:
    print(f'[{i}] year={q["year"]} ans={q["answer"]}')
    print(f'  Q: {q["question"][:80]}')
    for k in 'ABCD':
        print(f'  {k}: {q["options"].get(k,"")}')
    print()

# 6. 業務員被廢止/停止招攬
print('\n=== 業務員處分相關 (廢止/停止招攬) ===')
proc_qs = [(i,q) for i,q in law_qs if ('廢止' in q['question'] or '停止招攬' in q['question']) and '年' in q['question']]
for i, q in proc_qs[:8]:
    print(f'[{i}] year={q["year"]} ans={q["answer"]}')
    print(f'  Q: {q["question"][:80]}')
    for k in 'ABCD':
        print(f'  {k}: {q["options"].get(k,"")}')
    print()

# 7. 年度教育訓練時數/規定
print('\n=== 業務員教育訓練時數 ===')
train_qs = [(i,q) for i,q in law_qs if '教育訓練' in q['question'] and ('小時' in q['question'] or '時數' in q['question'] or '小時' in ' '.join(q['options'].values()))]
for i, q in train_qs[:8]:
    print(f'[{i}] year={q["year"]} ans={q["answer"]}')
    print(f'  Q: {q["question"][:80]}')
    for k in 'ABCD':
        print(f'  {k}: {q["options"].get(k,"")}')
    print()

# 8. 保證金額 (業務員管理規則中的保證金相關規定)
print('\n=== 保險業保證金/資本 ===')
bond_qs = [(i,q) for i,q in law_qs if '保證金' in q['question'] or '最低資本' in q['question']]
for i, q in bond_qs[:5]:
    print(f'[{i}] year={q["year"]} ans={q["answer"]}')
    print(f'  Q: {q["question"][:80]}')
    for k in 'ABCD':
        print(f'  {k}: {q["options"].get(k,"")}')
    print()

print(f'\n=== 確定過時題目數量: {len(OUTDATED_IDS)} ===')
sys.stdout.close()
print('Done', file=sys.stderr)
