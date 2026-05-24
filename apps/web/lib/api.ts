const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

export async function getHealth() {
  const res = await fetch(`${API_BASE}/api/v1/health`)
  return res.json()
}

export async function getDraws(limit = 20, offset = 0) {
  const res = await fetch(`${API_BASE}/api/v1/draws?limit=${limit}&offset=${offset}`)
  return res.json()
}

export async function getDraw(drawDate: number) {
  const res = await fetch(`${API_BASE}/api/v1/draws/${drawDate}`)
  return res.json()
}

export async function getFrequency(window = 0) {
  const res = await fetch(`${API_BASE}/api/v1/statistics/frequency?window=${window}`)
  return res.json()
}

export async function generateTicket(mode: 'xgboost' | 'random' = 'xgboost') {
  const res = await fetch(`${API_BASE}/api/v1/generator/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode })
  })
  return res.json()
}
