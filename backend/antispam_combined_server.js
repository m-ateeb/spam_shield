// Combined Antispam server (single-file) — no external deps
// Exposes:
//  GET  /health
//  GET  /api/reputation?url=...
//  POST /api/decision   { reputation, validation }
//  POST /api/quarantine { email }
//  GET  /api/quarantine

const http = require('http')
const fs = require('fs')
const path = require('path')

const PORT = process.env.ANTISPAM_PORT || 5001
const QUARANTINE_STORE = path.join(__dirname, 'antispam_quarantine.json')

function sendJson(res, status, obj) {
  const body = JSON.stringify(obj)
  res.writeHead(status, {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(body),
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
  })
  res.end(body)
}

function parseQuery(url) {
  const idx = url.indexOf('?')
  if (idx === -1) return {}
  return Object.fromEntries(new URLSearchParams(url.slice(idx + 1)))
}

function readJsonBody(req) {
  return new Promise((resolve, reject) => {
    let data = ''
    req.on('data', (chunk) => { data += chunk })
    req.on('end', () => {
      if (!data) return resolve(null)
      try { resolve(JSON.parse(data)) } catch (err) { reject(err) }
    })
    req.on('error', reject)
  })
}

// Decision engine (from analyzer README / earlier implementation)
function computeScore(reputation, validation) {
  const validationWeight = 0.6
  const providersWeight = 0.4
  const validationScore = (validation && typeof validation.score === 'number') ? validation.score : 0.5
  const providers = ['safeBrowsing', 'phishTank', 'urlScan']
  let providerScores = providers.map((k) => reputation && reputation[k] && reputation[k].safe ? 1 : 0)
  const avgProvider = providerScores.reduce((a,b) => a+b, 0) / providers.length
  return validationScore * validationWeight + avgProvider * providersWeight
}

function pickConfidence(score) {
  if (score > 0.85) return 'high'
  if (score > 0.6) return 'medium'
  return 'low'
}

function makeDecision(reputation, validation) {
  const score = computeScore(reputation, validation)
  const confidence = pickConfidence(score)
  let classification = 'suspicious'
  if (score > 0.85) classification = 'safe'
  if (score < 0.4) classification = 'malicious'
  const evidence = []
  if (!reputation) evidence.push('no-reputation')
  else {
    Object.entries(reputation).forEach(([k, v]) => {
      if (v && v.safe === false) evidence.push(`${k}:untrusted`)
    })
  }
  return { classification, score: Number(score.toFixed(3)), confidence, evidence }
}

// Quarantine store helpers (simple file-backed array)
function readQuarantine() {
  try {
    const raw = fs.readFileSync(QUARANTINE_STORE, 'utf8')
    return JSON.parse(raw || '[]')
  } catch (err) {
    return []
  }
}

function writeQuarantine(list) {
  fs.writeFileSync(QUARANTINE_STORE, JSON.stringify(list, null, 2), 'utf8')
}

const server = http.createServer(async (req, res) => {
  // CORS preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    })
    return res.end()
  }

  const url = req.url || '/'

  try {
    if (req.method === 'GET' && url.startsWith('/health')) {
      return sendJson(res, 200, { ok: true })
    }

    if (req.method === 'GET' && url.startsWith('/api/reputation')) {
      const q = parseQuery(url)
      const queryUrl = q.url || q.u || ''
      if (!queryUrl) return sendJson(res, 400, { error: 'missing url query param' })
      const now = new Date().toISOString()
      const normalized = {
        safeBrowsing: { safe: true, raw: { note: 'stubbed', url: queryUrl } },
        phishTank: { safe: true, raw: { note: 'stubbed' } },
        urlScan: { safe: true, raw: { note: 'stubbed' } },
        timestamp: now
      }
      return sendJson(res, 200, normalized)
    }

    if (req.method === 'POST' && url.startsWith('/api/decision')) {
      const body = await readJsonBody(req)
      const reputation = body && body.reputation
      const validation = body && body.validation
      const dec = makeDecision(reputation, validation)
      return sendJson(res, 200, dec)
    }

    if (req.method === 'POST' && url.startsWith('/api/quarantine')) {
      const body = await readJsonBody(req)
      if (!body || !body.email) return sendJson(res, 400, { error: 'missing email in body' })
      const list = readQuarantine()
      const entry = { id: Date.now(), email: body.email, addedAt: new Date().toISOString() }
      list.push(entry)
      writeQuarantine(list)
      return sendJson(res, 201, entry)
    }

    if (req.method === 'GET' && url.startsWith('/api/quarantine')) {
      const list = readQuarantine()
      return sendJson(res, 200, list)
    }

    // Not found
    return sendJson(res, 404, { error: 'not found' })
  } catch (err) {
    return sendJson(res, 500, { error: String(err && err.message ? err.message : err) })
  }
})

server.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`Antispam combined server listening on http://localhost:${PORT}`)
})
