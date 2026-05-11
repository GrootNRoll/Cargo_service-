import type { LoginResponse, OrderStatus } from "../types";

const useRelative = import.meta.env.VITE_USE_RELATIVE_API === "true";
const rawEnv = import.meta.env.VITE_API_URL as string | undefined;
const explicitUrl = rawEnv?.trim() ? rawEnv.trim().replace(/\/$/, "") : undefined;

/**
 * Базовый префикс API (заканчивается на `/api`).
 * — В dev без VITE_API_URL: `/api` (прокси Vite → 127.0.0.1:8000).
 * — Если в VITE_API_URL уже указан .../api — не дублируем.
 */
function apiPrefix(): string {
  if (useRelative) {
    return "/api";
  }
  if (explicitUrl) {
    const lower = explicitUrl.toLowerCase();
    if (lower.endsWith("/api")) {
      return explicitUrl;
    }
    return `${explicitUrl}/api`;
  }
  if (import.meta.env.DEV) {
    return "/api";
  }
  return "http://127.0.0.1:8000/api";
}

const API = apiPrefix();

const TOKEN_KEY = "wms_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export function redirectToLogin(): void {
  if (!window.location.pathname.startsWith("/login")) {
    window.location.assign("/login");
  }
}

function authHeaders(): Record<string, string> {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

type FetchOpts = {
  method?: string;
  body?: unknown;
  auth?: boolean;
};

async function parseError(res: Response): Promise<string> {
  try {
    const data: unknown = await res.json();
    if (data && typeof data === "object" && "detail" in data) {
      const detail = (data as { detail: unknown }).detail;
      if (typeof detail === "string") return detail;
      if (Array.isArray(detail)) {
        return detail
          .map((item) => {
            if (item && typeof item === "object" && "msg" in item) {
              return String((item as { msg: unknown }).msg);
            }
            return JSON.stringify(item);
          })
          .join("; ");
      }
    }
  } catch {
    /* empty */
  }
  if (res.status === 404) {
    return `Не найдено (${res.url}). Проверьте, что API запущен и адрес верный.`;
  }
  return res.statusText || "Ошибка запроса";
}

async function request<T>(path: string, opts: FetchOpts = {}): Promise<T> {
  const { method = "GET", body, auth = true } = opts;
  const headers: Record<string, string> = {};
  if (auth) Object.assign(headers, authHeaders());
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  const url = `${API}${path.startsWith("/") ? path : `/${path}`}`;
  const res = await fetch(url, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (res.status === 401 && auth) {
    setToken(null);
    redirectToLogin();
  }
  if (!res.ok) throw new Error(await parseError(res));
  if (res.status === 204) return undefined as T;
  if (method === "DELETE") return undefined as T;
  return res.json() as Promise<T>;
}

export async function apiGet<T>(path: string): Promise<T> {
  return request<T>(path, { auth: true });
}

export async function apiPostEmpty(path: string): Promise<void> {
  await request<void>(path, { method: "POST", auth: true });
}

/** POST без тела, ответ JSON. */
export async function apiPostForJson<T>(path: string): Promise<T> {
  return request<T>(path, { method: "POST", auth: true });
}

export async function apiPostJson<T>(path: string, body: unknown, auth = true): Promise<T> {
  return request<T>(path, { method: "POST", body, auth });
}

export async function apiPatchJson<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: "PATCH", body, auth: true });
}

export async function apiDelete(path: string): Promise<void> {
  await request<void>(path, { method: "DELETE", auth: true });
}

export function loginRequest(username: string, password: string): Promise<LoginResponse> {
  return apiPostJson<LoginResponse>(
    "/auth/login",
    { username, password },
    false,
  );
}

export function transitionOrder(orderId: number, toStatus: OrderStatus) {
  return apiPostJson(`/orders/${orderId}/transition`, { to_status: toStatus });
}
