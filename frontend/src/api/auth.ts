import { request } from "./client";

export type RegisterPayload = {
  username: string;
  password: string;
};

export async function registerUser(payload: RegisterPayload) {
  return request<{ id: number; username: string }>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type LoginResponse = {
  access_token: string;
  token_type: string;
};

export async function loginUser(username: string, password: string) {
  const body = new URLSearchParams();
  body.append("username", username);
  body.append("password", password);

  const res = await fetch(`${import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body,
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error((data && (data.detail || data.message)) || res.statusText);
  }
  return data as LoginResponse;
}
