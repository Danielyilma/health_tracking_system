import { request, withAuth } from "./client";

export type HealthRecord = {
  id: number;
  username: string;
  steps: number;
  sleep_hours: number;
  weight: number;
  timestamp: string;
};

export type CreateHealthRecord = {
  username: string;
  steps: number;
  sleep_hours: number;
  weight: number;
};

export type UpdateHealthRecord = Partial<Omit<CreateHealthRecord, "username">>;

export async function listHealthRecords(username: string, token?: string) {
  return request<HealthRecord[]>(`/health/data?username=${encodeURIComponent(username)}`, {
    headers: withAuth({}, token),
  });
}

export async function createHealthRecord(payload: CreateHealthRecord, token?: string) {
  return request<HealthRecord>(`/health/data`, {
    method: "POST",
    headers: withAuth({}, token),
    body: JSON.stringify(payload),
  });
}

export async function updateHealthRecord(id: number, payload: UpdateHealthRecord, token?: string) {
  return request<HealthRecord>(`/health/data/${id}`, {
    method: "PATCH",
    headers: withAuth({}, token),
    body: JSON.stringify(payload),
  });
}

export async function deleteHealthRecord(id: number, token?: string) {
  return request<{ message: string }>(`/health/data/${id}`, {
    method: "DELETE",
    headers: withAuth({}, token),
  });
}
