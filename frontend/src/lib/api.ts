/** Cliente da API AION com renovação automática de token. */
const BASE = import.meta.env.VITE_API_URL || "";

export function getTokens() {
  return {
    access: sessionStorage.getItem("aion_access"),
    refresh: sessionStorage.getItem("aion_refresh"),
  };
}

export function setTokens(access: string, refresh: string) {
  sessionStorage.setItem("aion_access", access);
  sessionStorage.setItem("aion_refresh", refresh);
}

export function clearTokens() {
  sessionStorage.removeItem("aion_access");
  sessionStorage.removeItem("aion_refresh");
}

async function tryRefresh(): Promise<boolean> {
  const { refresh } = getTokens();
  if (!refresh) return false;
  const r = await fetch(`${BASE}/api/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });
  if (!r.ok) { clearTokens(); return false; }
  const t = await r.json();
  setTokens(t.access_token, t.refresh_token);
  return true;
}

export async function api(path: string, options: RequestInit = {}, retry = true): Promise<any> {
  const { access } = getTokens();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (access) headers.Authorization = `Bearer ${access}`;
  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (res.status === 401 && retry && (await tryRefresh())) {
    return api(path, options, false);
  }
  if (res.status === 204) return null;
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || `Erro ${res.status}`);
  return body;
}

export async function login(email: string, password: string) {
  const form = new URLSearchParams({ username: email, password });
  const r = await fetch(`${BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form,
  });
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(body.detail || "Falha no login");
  setTokens(body.access_token, body.refresh_token);
  return body;
}
