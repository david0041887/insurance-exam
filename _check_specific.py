import json, sys
sys.stdout = open(r'C:\Users\david\insurance-exam\_specific.txt', 'w', encoding='utf-8')

with open(r'C:\Users\david\insurance-exam\questions.json', 'r', encoding='utf-8') as f:
    qs = json.load(f)

def show(i):
    q = qs[i]
    print(f'[{i}] year={q["year"]} section={q["section"]} ans={q["answer"]}')
    print(f'  Q: {q["question"]}')
    for k in 'ABCD':
        v = q['options'].get(k,'')
        mark = ' <<<<' if k == q['answer'] else ''
        print(f'  {k}: {v}{mark}')
    print()

# 1. year=99 遲延利息 question (flagged as 年利二分/三分)
print('=== 年利二分/三分 出現的題目 ===')
for i, q in enumerate(qs):
    text = q['question'] + ' ' + ' '.join(q['options'].values())
    if '年利二分' in text or '年利三分' in text:
        show(i)

# 2. year=101 通知期限
print('=== 年101 通知期限題 ===')
for i, q in enumerate(qs):
    if q['year'] == 101 and '通知' in q['question'] and '保險法所規定' in q['question']:
        show(i)

# 3. year=104 explicitly referencing old law
print('=== 明確引用 104年2月4日修正 ===')
for i, q in enumerate(qs):
    text = q['question'] + ' ' + ' '.join(q['options'].values())
    if '104 年 2 月 4 日' in text or '104年2月4日' in text:
        show(i)

# 4. year=104 催告天數 (check if answer matches current 30日)
print('=== year=104 催告/停效 題 ===')
for i, q in enumerate(qs):
    if q['year'] == 104 and '催告' in q['question'] and '停止效力' in q['question']:
        show(i)

# 5. Any question where answer references 年利二分 or 年利三分
print('=== 答案選項含舊利率 ===')
for i, q in enumerate(qs):
    ans = q['answer']
    ans_text = q['options'].get(ans, '')
    if '二分' in ans_text and ('年利' in ans_text or '利息' in q['question']):
        show(i)

# 6. 三個月 停效 old rule questions
print('=== 選項中催告期間非30日的停效題 ===')
for i, q in enumerate(qs):
    if ('停止效力' in q['question'] or '停效' in q['question']) and '催告' in q['question']:
        ans = q['answer']
        ans_text = q['options'].get(ans, '')
        # show if answer is not 30日
        if '30' not in ans_text and '三十' not in ans_text:
            show(i)

sys.stdout.close()
print('Done', file=sys.stderr)
