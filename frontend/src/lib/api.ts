/** Cliente da API AION com renovação automática de token. */
const configuredApi = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");
// Production always uses the official Vercel origin and its audited rewrites.
// This prevents a stale dashboard variable from bypassing the single-domain
// policy, Vercel edge caching and same-origin browser protections.
export const API_BASE = import.meta.env.PROD ? "" : configuredApi;

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
  const r = await fetch(`${API_BASE}/api/auth/refresh`, {
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
  const headers: Record<string, string> = { ...(options.headers as Record<string, string>) };
  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  if (access) headers.Authorization = `Bearer ${access}`;
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401 && retry && (await tryRefresh())) {
    return api(path, options, false);
  }
  if (res.status === 204) return null;
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || `Request failed (${res.status})`);
  return body;
}

export async function login(email: string, password: string) {
  const form = new URLSearchParams({ username: email, password });
  const r = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form,
  });
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(body.detail || "Sign-in failed");
  setTokens(body.access_token, body.refresh_token);
  return body;
}

export async function uploadEditorialImage(file: File, title: string) {
  const { access } = getTokens();
  const body = new FormData();
  body.append("image", file);
  const response = await fetch(
    `${API_BASE}/api/orchestrator/upload-image?title=${encodeURIComponent(title || "AION")}`,
    { method: "POST", headers: access ? { Authorization: `Bearer ${access}` } : {}, body },
  );
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || `Upload failed (${response.status})`);
  return payload;
}
