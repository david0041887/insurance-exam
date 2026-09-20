import json, re, sys
from collections import defaultdict
sys.stdout = open(r'C:\Users\david\insurance-exam\_all_topics.txt', 'w', encoding='utf-8')

with open(r'C:\Users\david\insurance-exam\questions.json', 'r', encoding='utf-8') as f:
    qs = json.load(f)

SECTIONS = {
    '保險學概要': [q for q in qs if q['section'] == '保險學概要'],
    '保險法規概要': [q for q in qs if '保險法規概要' in q['section'] and '現行法令' not in q['section']],
    '人身保險行銷概要': [q for q in qs if q['section'] == '人身保險行銷概要'],
    '財產保險行銷概要': [q for q in qs if q['section'] == '財產保險行銷概要'],
    '財產風險管理概要': [q for q in qs if q['section'] == '財產風險管理概要'],
    '人身風險管理概要': [q for q in qs if q['section'] == '人身風險管理概要'],
}

# ─── 各科年度分布 ───
for sec, sq in SECTIONS.items():
    print(f'\n{"="*60}')
    print(f'【{sec}】共 {len(sq)} 題')
    yrd = defaultdict(int)
    for q in sq:
        yrd[q['year']] += 1
    print('年份分布: ' + ', '.join(f"{y}:{c}" for y,c in sorted(yrd.items())))

# ─── 保險學概要 細項分析 ───
print('\n\n' + '='*60)
print('【保險學概要】細部考點')
ins_topics = {
    '保險契約原則': ['最大誠信', '誠信原則', '保險利益原則', '損害補償原則', '代位原則', '分攤原則'],
    '保險費計算': ['純保費', '附加保費', '總保費', '費率', '損失率', '賠付率'],
    '保險市場/組織': ['保險公司', '相互保險', '勞合社', 'Lloyd', '再保險公司'],
    '風險管理': ['風險', '風險管理', '損失控制', '風險迴避', '風險自留', '風險移轉'],
    '人壽保險': ['人壽保險', '終身壽險', '定期壽險', '養老保險'],
    '健康/傷害': ['健康保險', '傷害保險', '醫療保險', '失能'],
    '年金': ['年金', '即期年金', '遞延年金'],
    '財產保險': ['火災保險', '汽車保險', '工程保險', '責任保險', '海上保險'],
    '社會保險': ['社會保險', '勞工保險', '全民健保', '國民年金'],
    '保險監理': ['監理', '清償能力', '資本適足', '保險安定基金'],
    '再保險': ['再保險', '比例再保險', '超額再保險', '火災再保險', '溢額再保險'],
}
sec_qs = SECTIONS['保險學概要']
recent_qs = [q for q in sec_qs if q['year'] >= 108]
for topic, kws in ins_topics.items():
    cnt = sum(1 for q in recent_qs
              if any(kw in q['question'] or any(kw in v for v in q['options'].values())
                     for kw in kws))
    if cnt > 0:
        print(f'  {topic}: {cnt}')

# ─── 人身保險行銷概要 細項 ───
print('\n\n' + '='*60)
print('【人身保險行銷概要】細部考點')
life_mkt_topics = {
    '商品知識': ['利率變動型', '投資型', '分紅保單', '還本型', '定期壽險', '終身壽險'],
    '行銷理論': ['行銷組合', '4P', 'AIDA', '需求分析', '行銷管理'],
    '產品生命週期': ['產品生命週期', '導入期', '成長期', '成熟期', '衰退期'],
    '消費者行為': ['消費者行為', '購買動機', '需求層次', 'Maslow'],
    '通路/銀保': ['銀行保險', '通路', '業務員', '電話行銷', '網路投保'],
    '服務品質': ['服務品質', 'SERVQUAL', '顧客滿意', '客訴'],
    '招攬規範': ['招攬', '說明義務', '不當銷售', '回佣', '紅利'],
    '核保理賠': ['核保', '理賠', '帶病投保', '逆選擇'],
    '保單年齡': ['保單年齡', '年齡計算', '契約年齡'],
    '保費計算': ['保費計算', '純保費', '附加費用率'],
}
sec_qs = SECTIONS['人身保險行銷概要']
recent_qs = [q for q in sec_qs if q['year'] >= 108]
for topic, kws in life_mkt_topics.items():
    cnt = sum(1 for q in recent_qs
              if any(kw in q['question'] or any(kw in v for v in q['options'].values())
                     for kw in kws))
    if cnt > 0:
        print(f'  {topic}: {cnt}')

# ─── 財產保險行銷概要 ───
print('\n\n' + '='*60)
print('【財產保險行銷概要】細部考點')
prop_mkt_topics = {
    '火災保險商品': ['火災保險', '住宅火險', '商業火險'],
    '汽車保險': ['汽車保險', '強制汽責險', '任意汽車', '車輛損失險', '竊盜險'],
    '責任保險': ['責任保險', '公共意外責任', '產品責任', '專業責任'],
    '海上保險': ['海上保險', '海上貨物', '船殼保險'],
    '工程保險': ['工程保險', '營造綜合險', '安裝工程'],
    '意外險/傷害': ['傷害保險', '旅遊平安', '意外傷害'],
    '核保實務': ['核保', '費率', '損失率', '自負額'],
    '行銷通路': ['通路', '業務員', '代理人', '經紀人', '銀保'],
    '產品生命週期': ['產品生命週期'],
    '理賠實務': ['理賠', '損失估計', '公證人', '鑑定'],
}
sec_qs = SECTIONS['財產保險行銷概要']
recent_qs = [q for q in sec_qs if q['year'] >= 108]
for topic, kws in prop_mkt_topics.items():
    cnt = sum(1 for q in recent_qs
              if any(kw in q['question'] or any(kw in v for v in q['options'].values())
                     for kw in kws))
    if cnt > 0:
        print(f'  {topic}: {cnt}')

# ─── 財產風險管理概要 ───
print('\n\n' + '='*60)
print('【財產風險管理概要】細部考點')
prop_rm_topics = {
    '風險基本概念': ['風險定義', '純粹風險', '投機風險', '靜態風險', '動態風險', '主觀風險', '客觀風險'],
    '風險管理流程': ['風險辨識', '風險衡量', '風險評估', '風險處理', '風險監控'],
    '損失衡量': ['損失頻率', '損失幅度', '最大可能損失', 'MPL', '最大預期損失'],
    '風險管理工具': ['風險迴避', '損失控制', '風險自留', '風險移轉', '風險融資'],
    '自留/自保': ['自留', '自保', '自保公司', '專屬保險公司', 'Captive'],
    '企業風險管理': ['企業風險管理', 'ERM', '整合性風險管理'],
    '能量釋放理論': ['能量釋放', 'Haddon', '骨牌理論', 'Heinrich', '因果'],
    '保險需求': ['保險需求', '可保風險', '大數法則', '損失集中'],
    '財產損失': ['財產損失', '有形資產', '無形資產', '淨利損失'],
    '責任損失': ['責任損失', '侵權行為', '產品責任'],
}
sec_qs = SECTIONS['財產風險管理概要']
recent_qs = [q for q in sec_qs if q['year'] >= 108]
for topic, kws in prop_rm_topics.items():
    cnt = sum(1 for q in recent_qs
              if any(kw in q['question'] or any(kw in v for v in q['options'].values())
                     for kw in kws))
    if cnt > 0:
        print(f'  {topic}: {cnt}')

# ─── 人身風險管理概要 ───
print('\n\n' + '='*60)
print('【人身風險管理概要】細部考點')
life_rm_topics = {
    '人身風險種類': ['死亡風險', '失能風險', '長壽風險', '健康風險', '老年風險'],
    '死亡損失衡量': ['生命價值法', '遺族需求法', '人力資本', '未來收入'],
    '失能/殘廢': ['失能', '殘廢', '失業', '殘廢程度', '1-11級'],
    '長壽風險': ['長壽風險', '老年安養', '退休'],
    '社會保險': ['勞工保險', '全民健保', '國民年金', '就業保險'],
    '生命表': ['生命表', '死亡率', '生存率', '平均餘命'],
    '風險管理工具': ['人壽保險', '健康保險', '傷害保險', '年金保險'],
    '能量釋放': ['能量釋放', 'Haddon', '骨牌理論'],
    '保險規劃': ['保險規劃', '需求分析', '保障缺口'],
    '家庭生命週期': ['家庭生命週期', '新婚期', '育兒期', '空巢期', '退休期'],
}
sec_qs = SECTIONS['人身風險管理概要']
recent_qs = [q for q in sec_qs if q['year'] >= 108]
for topic, kws in life_rm_topics.items():
    cnt = sum(1 for q in recent_qs
              if any(kw in q['question'] or any(kw in v for v in q['options'].values())
                     for kw in kws))
    if cnt > 0:
        print(f'  {topic}: {cnt}')

# ─── 各科近年答案分布（A/B/C/D） ───
print('\n\n' + '='*60)
print('各科近年(110-114)答案分布（供選答猜測參考）')
for sec, sq in SECTIONS.items():
    recent = [q for q in sq if q['year'] >= 110]
    ans_cnt = defaultdict(int)
    for q in recent:
        ans_cnt[q['answer']] += 1
    total = sum(ans_cnt.values())
    print(f'  {sec}: ' + ', '.join(f'{k}:{v}({v/total*100:.0f}%)' for k,v in sorted(ans_cnt.items())))

sys.stdout.close()
print('Done', file=sys.stderr)
