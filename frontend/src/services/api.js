const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!response.ok) throw new Error(`Erro ${response.status}`)
  return response.json()
}

export const api = {
  health: () => request('/health'),
  tasks: () => request('/tasks'),
  logs: () => request('/logs'),
  memory: () => request('/memory'),
  createTask: (description) => request('/tasks', { method: 'POST', body: JSON.stringify({ description }) }),
  runTask: (id) => request(`/tasks/${id}/run`, { method: 'POST' }),
  getTask: (id) => request(`/tasks/${id}`),
  getReport: (id) => request(`/tasks/${id}/report`),
}
