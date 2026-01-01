import { request, withAuth } from "./client";

export type AnalyticsStats = {
  id: number;
  username: string;
  total_steps: number;
  record_count: number;
  average_steps: number;
};

export async function getStats(username: string, token?: string) {
  return request<AnalyticsStats>(`/analytics/stats/${encodeURIComponent(username)}`, {
    headers: withAuth({}, token),
  });
}
