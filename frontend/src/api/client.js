const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`)
  return res.json()
}

export async function predictGame(data) {
  const res = await fetch(`${API_BASE}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail?.[0]?.msg || `Predict failed: ${res.status}`)
  }
  return res.json()
}

export async function getStrategy(data) {
  const res = await fetch(`${API_BASE}/strategy`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail?.[0]?.msg || `Strategy failed: ${res.status}`)
  }
  return res.json()
}

export async function listModels() {
  const res = await fetch(`${API_BASE}/models`)
  if (!res.ok) throw new Error(`Models failed: ${res.status}`)
  return res.json()
}

export const API_BASE_URL = API_BASE
