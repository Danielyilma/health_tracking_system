const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  if (res.status === 204) return {} as T;

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const message = (data && (data.detail || data.message)) || res.statusText;
    throw new Error(message);
  }

  return data as T;
}

export function withAuth(headers: Record<string, string>, token?: string) {
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export { request };
