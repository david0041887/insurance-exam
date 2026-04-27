// 保險經紀人考試 AI Worker
//
// POST /grade   { question, answer }  -> 申論題批改
// GET  /health  -> { ok: true }

const ALLOWED_ORIGINS = [
  'https://david0041887.github.io',
  'http://localhost:8080',
  'http://127.0.0.1:8080',
];

const MODEL = 'claude-haiku-4-5-20251001';

const ipCounts = new Map();
function getTodayStr() {
  const d = new Date();
  return d.getUTCFullYear() + '-' + String(d.getUTCMonth()+1).padStart(2,'0') + '-' + String(d.getUTCDate()).padStart(2,'0');
}
function checkRateLimit(ip, suffix, limit) {
  const key = ip + ':' + suffix + ':' + getTodayStr();
  const cur = ipCounts.get(key) || 0;
  if (cur >= limit) return false;
  ipCounts.set(key, cur + 1);
  if (ipCounts.size > 2000) {
    const today = getTodayStr();
    for (const k of ipCounts.keys()) { if (!k.endsWith(today)) ipCounts.delete(k); }
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

// GRADE -----------------------------------------------------------------------
const GRADE_SYSTEM = `你是台灣保險經紀人國家考試的資深閱卷委員，熟稔《保險法》全文與相關子法。批改申論題，滿分25分。你必須呼叫 grade_essay 工具回傳評分結果。`;

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
          structure:  { type: 'number', minimum: 0, maximum: 5 },
          citations:  { type: 'number', minimum: 0, maximum: 8 },
          reasoning:  { type: 'number', minimum: 0, maximum: 8 },
          doctrine:   { type: 'number', minimum: 0, maximum: 3 },
          conclusion: { type: 'number', minimum: 0, maximum: 1 },
        },
        required: ['structure','citations','reasoning','doctrine','conclusion'],
      },
      strengths:       { type: 'array', items: { type: 'string' } },
      weaknesses:      { type: 'array', items: { type: 'string' } },
      suggestions:     { type: 'array', items: { type: 'string' } },
      missedKeyPoints: { type: 'array', items: { type: 'string' } },
    },
    required: ['totalScore','breakdown','strengths','weaknesses','suggestions','missedKeyPoints'],
  },
};

async function gradeEssay(question, answer, apiKey) {
  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'x-api-key': apiKey, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
    body: JSON.stringify({
      model: MODEL, max_tokens: 1200, system: GRADE_SYSTEM,
      tools: [GRADE_TOOL], tool_choice: { type: 'tool', name: 'grade_essay' },
      messages: [{ role: 'user', content: '【題目】\n' + question + '\n\n【作答】\n' + answer + '\n\n請呼叫 grade_essay 工具。' }],
    }),
  });
  if (!res.ok) throw new Error('API error ' + res.status + ': ' + await res.text());
  const data = await res.json();
  const toolUse = (data.content||[]).find(b => b.type === 'tool_use');
  if (!toolUse) throw new Error('Model did not call grade_essay');
  const result = toolUse.input;
  result.usage = data.usage;
  return result;
}

// HANDLER ---------------------------------------------------------------------
export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const url = new URL(request.url);

    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: corsHeaders(origin) });
    if (url.pathname === '/health') return json({ ok: true, model: MODEL }, 200, origin);
    if (!env.ANTHROPIC_API_KEY) return json({ error: '伺服器未設定 ANTHROPIC_API_KEY' }, 500, origin);

    let body;
    try { body = await request.json(); } catch (_) { return json({ error: 'Invalid JSON' }, 400, origin); }

    const ip = request.headers.get('cf-connecting-ip') || 'unknown';

    // /grade
    if (url.pathname === '/grade' && request.method === 'POST') {
      const limit = parseInt(env.DAILY_LIMIT_PER_IP || '50', 10);
      if (!checkRateLimit(ip, 'gr', limit)) return json({ error: '今日批改額度已用完（每IP每日'+limit+'次）' }, 429, origin);
      const question = (body.question||'').trim();
      const answer   = (body.answer||'').trim();
      if (!question || !answer) return json({ error: '缺少 question 或 answer' }, 400, origin);
      if (answer.length < 50)   return json({ error: '作答太短（至少50字）' }, 400, origin);
      if (answer.length > 8000) return json({ error: '作答過長（上限8000字）' }, 400, origin);
      try {
        return json(await gradeEssay(question, answer, env.ANTHROPIC_API_KEY), 200, origin);
      } catch (err) {
        return json({ error: 'AI批改失敗：' + (err.message || String(err)) }, 502, origin);
      }
    }

    return json({ error: 'Not found' }, 404, origin);
  },
};
