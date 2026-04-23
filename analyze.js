// 分析 3937 題，找出常見題型 / 重複主題
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');

// 抓出 ALL_QUESTIONS = [...] 陣列
const m = html.match(/var ALL_QUESTIONS\s*=\s*(\[[\s\S]*?\]);/);
if (!m) { console.error('找不到 ALL_QUESTIONS'); process.exit(1); }
const questions = JSON.parse(m[1]);
console.log(`總題數：${questions.length}`);

// 把題目存成獨立 JSON 方便之後用
fs.writeFileSync(path.join(__dirname, 'questions.json'), JSON.stringify(questions, null, 2));

// --- 1. 按 section / type / year 分布 ---
const bySection = {};
const byType = {};
const byYear = {};
for (const q of questions) {
  bySection[q.section] = (bySection[q.section] || 0) + 1;
  byType[q.type] = (byType[q.type] || 0) + 1;
  byYear[q.year] = (byYear[q.year] || 0) + 1;
}

// --- 2. 從題幹抽出關鍵概念（用常見名詞 + 法律/保險術語 + 專有詞）---
// 定義一組「主題關鍵字」— 保險考試的常見核心概念
const topicKeywords = [
  // 保險法基礎
  '保險利益', '保險契約', '要保人', '被保險人', '受益人', '保險人', '保險代理人', '保險經紀人', '保險公證人',
  '保險費', '保險金額', '告知義務', '複保險', '再保險', '危險', '共保', '分保',
  '代位求償', '代位', '不可抗力', '免責', '除外責任', '契約撤銷', '契約無效', '契約終止', '契約解除',
  '除斥期間', '消滅時效', '時效',
  // 人身保險
  '人壽保險', '死亡保險', '生存保險', '生死合險', '年金保險', '健康保險', '傷害保險', '投資型保險',
  '定期壽險', '終身壽險', '養老保險', '團體保險',
  '保單價值準備金', '解約金', '保單借款', '紅利', '復效', '停效', '不喪失價值',
  '自殺', '自殘', '殘廢', '失能',
  // 財產保險
  '火災保險', '汽車保險', '強制汽車責任保險', '強制險', '任意險', '車體損失保險', '第三人責任保險',
  '海上保險', '責任保險', '工程保險', '運輸保險', '貨物保險', '船舶保險',
  '全損', '分損', '共同海損', '單獨海損', '施救費用',
  // 風險管理
  '風險管理', '風險辨識', '風險評估', '風險控制', '風險理財', '風險移轉', '風險自留', '損失頻率', '損失幅度',
  '純損風險', '投機風險', '可保風險', '大數法則', '逆選擇',
  // 數理 / 財務
  '準備金', '責任準備金', '未滿期保費', '賠款準備金', '特別準備金',
  '清償能力', 'RBC', '資本適足率', '淨值', '安定基金',
  // 實務
  '理賠', '核保', '招攬', '業務員', '佣金', '手續費', '專業責任', '說明義務',
  '洗錢', '個人資料', '消費者保護',
  // 法規
  '保險法', '保險業法', '民法', '公司法', '金融消費者保護法', '保險業務員管理規則',
];

function findTopics(text) {
  const found = [];
  for (const kw of topicKeywords) {
    if (text.includes(kw)) found.push(kw);
  }
  return found;
}

// 每題抽出主題
const questionTopics = questions.map((q, i) => ({
  i, q, topics: findTopics(q.question + ' ' + Object.values(q.options).join(' '))
}));

// --- 3. 統計每個主題出現次數 ---
const topicCount = {};
for (const { topics } of questionTopics) {
  for (const t of topics) topicCount[t] = (topicCount[t] || 0) + 1;
}

// --- 4. 題幹起首常見句型 (下列何者... / 關於... / 依XX規定 ...) ---
const stemPatternCount = {};
for (const q of questions) {
  const first = q.question.slice(0, 8);
  stemPatternCount[first] = (stemPatternCount[first] || 0) + 1;
}

// --- 5. section + topic 交叉 ---
const sectionTopic = {};
for (const { q, topics } of questionTopics) {
  sectionTopic[q.section] = sectionTopic[q.section] || {};
  for (const t of topics) {
    sectionTopic[q.section][t] = (sectionTopic[q.section][t] || 0) + 1;
  }
}

// --- 輸出報告 ---
function sortDesc(obj, limit = 30) {
  return Object.entries(obj).sort((a, b) => b[1] - a[1]).slice(0, limit);
}

const report = [];
report.push('# 保險考古題分析報告');
report.push(`\n**總題數：** ${questions.length}\n`);

report.push('## 1. 科目分布（section）');
for (const [k, v] of sortDesc(bySection, 50)) {
  report.push(`- ${k}: ${v} 題`);
}

report.push('\n## 2. 類別分布（type）');
for (const [k, v] of sortDesc(byType)) {
  report.push(`- ${k}: ${v} 題`);
}

report.push('\n## 3. 年度分布（民國）');
for (const [k, v] of Object.entries(byYear).sort((a, b) => b[0] - a[0])) {
  report.push(`- ${k}: ${v} 題`);
}

report.push('\n## 4. 最常出現的核心概念 Top 40');
for (const [k, v] of sortDesc(topicCount, 40)) {
  report.push(`- **${k}**: ${v} 題`);
}

report.push('\n## 5. 題幹常見起首（前 8 字）Top 20');
for (const [k, v] of sortDesc(stemPatternCount, 20)) {
  report.push(`- \`${k}...\`: ${v} 題`);
}

report.push('\n## 6. 各科目 Top 10 核心主題');
for (const section of Object.keys(sectionTopic)) {
  report.push(`\n### ${section}（共 ${bySection[section]} 題）`);
  for (const [k, v] of sortDesc(sectionTopic[section], 10)) {
    const pct = ((v / bySection[section]) * 100).toFixed(1);
    report.push(`- ${k}: ${v} 題 (${pct}%)`);
  }
}

fs.writeFileSync(path.join(__dirname, 'report.md'), report.join('\n'));
console.log('已寫入 report.md');

// 額外：每個 Top 主題挑 3 題代表題，方便「精選」
const topTopics = sortDesc(topicCount, 30).map(([k]) => k);
const curated = {};
for (const topic of topTopics) {
  const matches = questionTopics.filter(x => x.topics.includes(topic));
  // 取最新年度的前 3 題作為代表
  matches.sort((a, b) => b.q.year - a.q.year);
  curated[topic] = matches.slice(0, 3).map(x => ({
    year: x.q.year, section: x.q.section, question: x.q.question, answer: x.q.answer, options: x.q.options
  }));
}
fs.writeFileSync(path.join(__dirname, 'curated.json'), JSON.stringify(curated, null, 2));
console.log('已寫入 curated.json（每個 Top 主題的 3 題代表題）');
