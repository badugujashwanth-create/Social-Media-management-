export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000';

const API_PREFIX = '/api/v1';

export type ApiOptions = RequestInit & { auth?: boolean };

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export function getToken() {
  if (typeof window === 'undefined') return '';
  return localStorage.getItem('smcc_token') || '';
}

export function setToken(token: string) {
  if (typeof window === 'undefined') return;
  localStorage.setItem('smcc_token', token);
}

export function clearToken() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('smcc_token');
}

function trimTrailingSlashes(value: string): string {
  return value.replace(/\/+$/, '');
}

function isAbsoluteUrl(path: string): boolean {
  return /^https?:\/\//i.test(path);
}

function normalizePath(path: string): string {
  if (!path) return API_PREFIX;
  if (isAbsoluteUrl(path)) return path;

  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  if (cleanPath === '/health' || cleanPath.startsWith('/health?')) return cleanPath;
  if (cleanPath.startsWith('/api/')) return cleanPath;

  const baseHasApiPrefix = trimTrailingSlashes(API_BASE).endsWith(API_PREFIX);
  return baseHasApiPrefix ? cleanPath : `${API_PREFIX}${cleanPath}`;
}

export function resolveApiUrl(path: string): string {
  const normalizedPath = normalizePath(path);
  if (isAbsoluteUrl(normalizedPath)) return normalizedPath;
  return `${trimTrailingSlashes(API_BASE)}${normalizedPath}`;
}

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  headers.set('Content-Type', 'application/json');
  if (options.auth) {
    const token = getToken();
    if (token) headers.set('Authorization', `Bearer ${token}`);
  }

  const url = resolveApiUrl(path);

  let res: Response;
  try {
    res = await fetch(url, {
      ...options,
      headers,
      cache: 'no-store',
    });
  } catch {
    throw new ApiError(
      `Cannot reach API at ${url}. Start FastAPI on :8000 and set NEXT_PUBLIC_API_BASE.`,
      0,
    );
  }

  if (!res.ok) {
    let detail = 'Request failed';
    try {
      const body = await res.json();
      detail = body.detail || body.message || detail;
    } catch {}
    throw new ApiError(detail, res.status);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
