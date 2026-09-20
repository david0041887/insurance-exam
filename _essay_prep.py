import json, re, sys
from collections import defaultdict
sys.stdout = open(r'C:\Users\david\insurance-exam\_essay_report.txt', 'w', encoding='utf-8')

with open(r'C:\Users\david\insurance-exam\questions.json', 'r', encoding='utf-8') as f:
    qs = json.load(f)

# 統計各科近年題數分布（108年以後）
law_qs = [q for q in qs if '保險法規概要' in q.get('section','') and '現行法令' not in q.get('section','')]
recent = [q for q in law_qs if q['year'] >= 108]

# 統計高頻關鍵字
kw_count = defaultdict(int)
keywords = [
    '業務員', '保險費', '複保險', '再保險', '保險利益', '複保險', '解除契約', '保險人',
    '要保人', '被保險人', '受益人', '保險代理人', '保險經紀人', '保險公證人',
    '保費', '停效', '復效', '遲延利息', '告知義務', '通知義務', '資本適足率',
    '分紅', '年金', '人壽保險', '健康保險', '傷害保險', '火災保險', '責任保險',
    '保險契約', '危險增加', '保單借款', '不實說明', '惡意複保險', '受益人變更',
    '指定受益人', '保險金請求', '理賠', '強制執行', '破產', '喪失保險費', '免責條款',
]
for q in recent:
    text = q['question']
    for kw in keywords:
        if kw in text:
            kw_count[kw] += 1

print('=== 108年後 保險法規概要 高頻考點 (題數) ===')
for kw, cnt in sorted(kw_count.items(), key=lambda x: -x[1])[:30]:
    print(f'  {kw}: {cnt}')

# 近5年 (110-114) 出題主題分析
print('\n=== 近5年 (110-114) 各年高頻考點 ===')
for yr in range(110, 115):
    yr_qs = [q for q in law_qs if q['year'] == yr]
    yr_kw = defaultdict(int)
    for q in yr_qs:
        for kw in keywords:
            if kw in q['question']:
                yr_kw[kw] += 1
    top5 = sorted(yr_kw.items(), key=lambda x: -x[1])[:8]
    print(f'  {yr}年: {", ".join(f"{k}({v})" for k,v in top5)}')

# 找出 考古題中「計算題型」或「申論式」的題目
print('\n=== 類似申論/計算考點 (有具體情境的綜合題) ===')
scenario_qs = [(i,q) for i,q in enumerate(qs)
    if '保險法規概要' in q.get('section','')
    and len(q['question']) > 100
    and any(x in q['question'] for x in ['甲', '乙', '丙', '丁', 'A公司', 'B公司', '案例'])]
print(f'共找到 {len(scenario_qs)} 題情境式考題')

# 近3年大題
print('\n近3年(112-114)情境式題目 前20題:')
recent_scenario = [(i,q) for i,q in scenario_qs if q['year'] >= 112]
for i, q in recent_scenario[:20]:
    print(f'  [{i}] year={q["year"]} Q: {q["question"][:100]}')

sys.stdout.close()
print('Done', file=sys.stderr)
