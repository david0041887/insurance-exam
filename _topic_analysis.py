import json, re, sys
from collections import defaultdict
sys.stdout = open(r'C:\Users\david\insurance-exam\_topic_detail.txt', 'w', encoding='utf-8')

with open(r'C:\Users\david\insurance-exam\questions.json', 'r', encoding='utf-8') as f:
    qs = json.load(f)

law_qs = [q for q in qs if '保險法規概要' in q.get('section','') and '現行法令' not in q.get('section','')]

# 細分主題分析
topics = {
    '複保險': ['複保險', '惡意複保險', '善意複保險'],
    '停效復效': ['停止效力', '停效', '恢復效力', '復效'],
    '保險利益': ['保險利益'],
    '告知義務': ['告知', '不實說明', '不為說明', '隱匿'],
    '危險增加': ['危險增加', '危險變更'],
    '遲延利息': ['遲延利息', '遲延給付'],
    '受益人': ['受益人', '指定受益人', '變更受益人'],
    '保單借款': ['保單借款', '質借'],
    '業務員登錄': ['登錄', '登錄證', '換發'],
    '業務員處分': ['停止招攬', '廢止', '撤銷.*登錄'],
    '業務員教育訓練': ['教育訓練', '在職訓練', '職前訓練'],
    '經紀人管理': ['保險經紀人.*規定', '執業證照', '經紀人.*許可'],
    '保費催告停效': ['催告', '屆.*日不交付'],
    '時效': ['時效', '請求權', '消滅時效'],
    '自殺條款': ['自殺', '故意自殺'],
    '火災保險': ['火災保險', '火災'],
    '傷害保險': ['傷害保險', '意外傷害'],
    '健康保險': ['健康保險', '醫療'],
    '年金保險': ['年金保險', '年金'],
    '契約無效': ['契約無效', '無效', '得撤銷'],
    '解除契約': ['解除契約', '終止契約'],
    '代位求償': ['代位', '代位求償'],
    '保險契約轉讓': ['轉讓', '所有權移轉'],
    '資本適足率': ['資本適足率', 'RBC'],
}

print('=== 各主題年度出題數 (108-114) ===')
header = 'topic'.ljust(16) + ''.join(f' {yr}' for yr in range(108, 115)) + '  合計'
print(header)
print('-' * 70)

topic_totals = {}
for topic, patterns in topics.items():
    row = topic.ljust(16)
    total = 0
    for yr in range(108, 115):
        yr_qs = [q for q in law_qs if q['year'] == yr]
        cnt = 0
        for q in yr_qs:
            text = q['question'] + ' ' + ' '.join(q['options'].values())
            if any(re.search(p, text) for p in patterns):
                cnt += 1
        row += f'  {cnt:2d}'
        total += cnt
    row += f'  {total:3d}'
    topic_totals[topic] = total
    print(row)

print('\n=== 按總題數排序 ===')
for topic, total in sorted(topic_totals.items(), key=lambda x: -x[1]):
    print(f'  {topic}: {total}')

# 分析最近有沒有出過的主題（可能是猜題重點）
print('\n=== 114年考點 (出題數) ===')
yr114 = [q for q in law_qs if q['year'] == 114]
for topic, patterns in topics.items():
    cnt = sum(1 for q in yr114
        if any(re.search(p, q['question'] + ' ' + ' '.join(q['options'].values()))
               for p in patterns))
    if cnt > 0:
        print(f'  {topic}: {cnt}')

sys.stdout.close()
print('Done', file=sys.stderr)
