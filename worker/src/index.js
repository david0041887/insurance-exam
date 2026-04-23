// 保險經紀人考試申論題 AI 批改 Worker
//
// POST /grade  { question, answer, profile? }  →  { score, maxScore, breakdown, feedback, reference? }
// GET  /health →  { ok: true }
//
// CORS is locked to the GitHub Pages origin (and localhost for dev).
// Per-IP daily rate limit via KV-less in-memory Map (resets when worker recycles).

const ALLOWED_ORIGINS = [
  'https://david0041887.github.io',
  'http://localhost:8080',
  'http://127.0.0.1:8080',
];

const MODEL = 'claude-haiku-4-5-20251001';
const MAX_TOKENS = 1200;

// Simple per-IP daily counter (best-effort; resets on worker recycle)
const ipCounts = new Map();
function getTodayStr() {
  const d = new Date();
  return d.getUTCFullYear() + '-' + String(d.getUTCMonth() + 1).padStart(2, '0') + '-' + String(d.getUTCDate()).padStart(2, '0');
}
function checkRateLimit(ip, limit) {
  const today = getTodayStr();
  const key = ip + ':' + today;
  const current = ipCounts.get(key) || 0;
  if (current >= limit) return false;
  ipCounts.set(key, current + 1);
  // Purge old entries
  if (ipCounts.size > 1000) {
    for (const k of ipCounts.keys()) {
      if (!k.endsWith(today)) ipCounts.delete(k);
    }
  }
  return true;
}

function corsHeaders(origin) {
  const allowed = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    'Access-Control-Allow-Origin': allowed,
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
  };
}

function json(data, status, origin) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...corsHeaders(origin) },
  });
}

const SYSTEM_PROMPT = `你是台灣保險經紀人國家考試的資深閱卷委員，熟稔《保險法》全文與相關子法、實務見解與學說。

你的任務是批改一份申論題作答，採用以下 rubric（滿分 25 分）：

【結構分 5 分】
- 是否使用大標(一、二、三…)→中標((一)(二)…)→小標(1、2…)→細項(①②)的層級
- 每個論點前是否有標題，便於閱卷快速抓分
- 結論是否單獨成段

【法條引用分 8 分】
- 是否精確引用條文到項/款(例：保§64 II、民§111)
- 引用的條文是否正確對應主張
- 是否涵蓋該題應引用的核心條文

【要件與涵攝分 8 分】
- 是否先解釋「意義」再論「要件」
- 要件拆分是否完整（客觀要件 vs 主觀要件、構成要件 vs 法律效果）
- 若為案例題，是否將法律規定「涵攝」到本案事實，並得出結論
- 是否指出爭點（若題目為法律爭議題）

【學理與論理分 3 分】
- 是否提及學說爭議（甲說/乙說/通說）
- 是否以「吾人以為」等方式表達立場
- 論理是否連貫、有無邏輯跳躍

【結論扣題分 1 分】
- 結論是否回應題目所問
- 結論是否分點整理

批改時：
1. 逐項計分（可給小數點 0.5）
2. 指出明顯缺漏（例：沒引到保險法第 X 條；結構混亂；案例未涵攝）
3. 給具體改善建議（不是空泛的「多練習」）
4. 如果作答完全離題或空白，給 0 分並說明原因

你必須呼叫 grade_essay 工具回傳評分結果，不要輸出純文字說明。`;

const GRADE_TOOL = {
  name: 'grade_essay',
  description: '回傳申論題批改結果',
  input_schema: {
    type: 'object',
    properties: {
      totalScore: { type: 'number', minimum: 0, maximum: 25 },
      breakdown: {
        type: 'object',
        properties: {
          structure: { type: 'number', minimum: 0, maximum: 5 },
          citations: { type: 'number', minimum: 0, maximum: 8 },
          reasoning: { type: 'number', minimum: 0, maximum: 8 },
          doctrine: { type: 'number', minimum: 0, maximum: 3 },
          conclusion: { type: 'number', minimum: 0, maximum: 1 },
        },
        required: ['structure', 'citations', 'reasoning', 'doctrine', 'conclusion'],
      },
      strengths: { type: 'array', items: { type: 'string' }, description: '作答優點，至少 1 項，最多 4 項' },
      weaknesses: { type: 'array', items: { type: 'string' }, description: '明顯缺漏，至少 1 項，最多 5 項' },
      suggestions: { type: 'array', items: { type: 'string' }, description: '具體改善建議，至少 1 項，最多 4 項' },
      missedKeyPoints: { type: 'array', items: { type: 'string' }, description: '應提到但未提的關鍵法條或概念' },
    },
    required: ['totalScore', 'breakdown', 'strengths', 'weaknesses', 'suggestions', 'missedKeyPoints'],
  },
};

async function gradeEssay(question, answer, apiKey) {
  const userMessage = `【題目】\n${question}\n\n【考生作答】\n${answer}\n\n請呼叫 grade_essay 工具回傳批改結果。`;

  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: MAX_TOKENS,
      system: SYSTEM_PROMPT,
      tools: [GRADE_TOOL],
      tool_choice: { type: 'tool', name: 'grade_essay' },
      messages: [{ role: 'user', content: userMessage }],
    }),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error('Anthropic API error ' + res.status + ': ' + errText);
  }

  const data = await res.json();
  const toolUse = (data.content || []).find(b => b.type === 'tool_use');
  if (!toolUse) throw new Error('Model did not call grade_essay tool');

  const result = toolUse.input;
  result.usage = data.usage;
  return result;
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const url = new URL(request.url);

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }

    if (url.pathname === '/health') {
      return json({ ok: true, model: MODEL }, 200, origin);
    }

    if (url.pathname !== '/grade' || request.method !== 'POST') {
      return json({ error: 'Not found' }, 404, origin);
    }

    // Rate limit
    const ip = request.headers.get('cf-connecting-ip') || 'unknown';
    const limit = parseInt(env.DAILY_LIMIT_PER_IP || '50', 10);
    if (!checkRateLimit(ip, limit)) {
      return json({ error: '今日批改額度已用完（每 IP 每日 ' + limit + ' 次）' }, 429, origin);
    }

    if (!env.ANTHROPIC_API_KEY) {
      return json({ error: '伺服器尚未設定 ANTHROPIC_API_KEY' }, 500, origin);
    }

    let body;
    try {
      body = await request.json();
    } catch (_) {
      return json({ error: 'Invalid JSON body' }, 400, origin);
    }

    const question = (body.question || '').trim();
    const answer = (body.answer || '').trim();
    if (!question || !answer) {
      return json({ error: '缺少 question 或 answer 欄位' }, 400, origin);
    }
    if (answer.length < 50) {
      return json({ error: '作答太短（至少需 50 字）' }, 400, origin);
    }
    if (answer.length > 8000) {
      return json({ error: '作答過長（上限 8000 字）' }, 400, origin);
    }

    try {
      const result = await gradeEssay(question, answer, env.ANTHROPIC_API_KEY);
      return json(result, 200, origin);
    } catch (err) {
      return json({ error: 'AI 批改失敗：' + (err.message || String(err)) }, 502, origin);
    }
  },
};