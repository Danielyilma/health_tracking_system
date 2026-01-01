import { useNavigate } from "@tanstack/react-router";
import { useAuth } from "../state/auth";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  HealthRecord,
  createHealthRecord,
  deleteHealthRecord,
  listHealthRecords,
  updateHealthRecord,
} from "../api/health";
import { getStats } from "../api/analytics";
import { FormEvent, useMemo, useState } from "react";

export function Dashboard() {
  const { auth } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  if (!auth) {
    navigate({ to: "/login" });
    return null;
  }

  const { data: records, isLoading, error } = useQuery({
    queryKey: ["records", auth.username],
    queryFn: () => listHealthRecords(auth.username, auth.token),
  });

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["stats", auth.username],
    queryFn: () => getStats(auth.username, auth.token),
    enabled: !!records?.length,
  });

  const createMutation = useMutation({
    mutationFn: (payload: { steps: number; sleep_hours: number; weight: number }) =>
      createHealthRecord({ ...payload, username: auth.username }, auth.token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["records", auth.username] });
      queryClient.invalidateQueries({ queryKey: ["stats", auth.username] });
      setForm({ steps: "", sleep_hours: "", weight: "" });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<HealthRecord> }) =>
      updateHealthRecord(id, payload, auth.token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["records", auth.username] });
      queryClient.invalidateQueries({ queryKey: ["stats", auth.username] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteHealthRecord(id, auth.token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["records", auth.username] });
      queryClient.invalidateQueries({ queryKey: ["stats", auth.username] });
    },
  });

  const [form, setForm] = useState({ steps: "", sleep_hours: "", weight: "" });
  const [editingId, setEditingId] = useState<number | null>(null);

  const sortedRecords = useMemo(() => {
    return (records || []).slice().sort((a, b) => (a.timestamp < b.timestamp ? 1 : -1));
  }, [records]);

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      steps: Number(form.steps),
      sleep_hours: Number(form.sleep_hours),
      weight: Number(form.weight),
    });
  };

  const startEdit = (rec: HealthRecord) => {
    setEditingId(rec.id);
    setForm({
      steps: String(rec.steps),
      sleep_hours: String(rec.sleep_hours),
      weight: String(rec.weight),
    });
  };

  const saveEdit = () => {
    if (!editingId) return;
    updateMutation.mutate({
      id: editingId,
      payload: {
        steps: Number(form.steps),
        sleep_hours: Number(form.sleep_hours),
        weight: Number(form.weight),
      },
    });
    setEditingId(null);
    setForm({ steps: "", sleep_hours: "", weight: "" });
  };

  return (
    <div className="hero">
      <div className="section-title">
        <h1>Dashboard</h1>
        <span className="badge">Signed in as {auth.username}</span>
      </div>

      <div className="grid" style={{ gridTemplateColumns: "2fr 1.2fr" }}>
        <div className="panel">
          <div className="section-title">
            <h2>Health Records</h2>
            <span className="badge">CRUD</span>
          </div>
          <form className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12 }} onSubmit={onSubmit}>
            <div>
              <label className="label">Steps</label>
              <input
                className="input"
                value={form.steps}
                onChange={(e) => setForm((f) => ({ ...f, steps: e.target.value }))}
                required
                type="number"
                min={0}
              />
            </div>
            <div>
              <label className="label">Sleep (hours)</label>
              <input
                className="input"
                value={form.sleep_hours}
                onChange={(e) => setForm((f) => ({ ...f, sleep_hours: e.target.value }))}
                required
                type="number"
                step="0.1"
                min={0}
              />
            </div>
            <div>
              <label className="label">Weight (kg)</label>
              <input
                className="input"
                value={form.weight}
                onChange={(e) => setForm((f) => ({ ...f, weight: e.target.value }))}
                required
                type="number"
                step="0.1"
                min={0}
              />
            </div>
            <div style={{ alignSelf: "end" }}>
              <button className="btn" type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? "Saving..." : "Add record"}
              </button>
            </div>
          </form>

          <div style={{ marginTop: 16 }}>
            {isLoading && <div className="status">Loading records...</div>}
            {error && <div className="status" style={{ color: "var(--danger)" }}>{(error as Error).message}</div>}
            {!isLoading && !error && (!records || records.length === 0) && (
              <div className="empty">No records yet. Add your first entry.</div>
            )}

            {sortedRecords.length > 0 && (
              <table className="table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Steps</th>
                    <th>Sleep</th>
                    <th>Weight</th>
                    <th>Time</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {sortedRecords.map((rec) => (
                    <tr key={rec.id}>
                      <td>{rec.id}</td>
                      <td>{rec.steps}</td>
                      <td>{rec.sleep_hours} h</td>
                      <td>{rec.weight} kg</td>
                      <td>{new Date(rec.timestamp).toLocaleString()}</td>
                      <td>
                        <div className="actions">
                          <button className="btn secondary" onClick={() => startEdit(rec)}>
                            Edit
                          </button>
                          <button
                            className="btn danger"
                            onClick={() => deleteMutation.mutate(rec.id)}
                            disabled={deleteMutation.isPending}
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        <div className="grid" style={{ gap: 14 }}>
          <div className="panel">
            <div className="section-title">
              <h2>Analytics</h2>
              <span className="badge">Average steps</span>
            </div>
            {statsLoading && <div className="status">Loading stats...</div>}
            {!statsLoading && !records?.length && (
              <div className="empty">Add records to see analytics.</div>
            )}
            {stats && (
              <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 12 }}>
                <div className="card">
                  <div className="label">Average steps</div>
                  <div className="chip">{stats.average_steps.toFixed(1)}</div>
                </div>
                <div className="card">
                  <div className="label">Total steps</div>
                  <div className="chip">{stats.total_steps}</div>
                </div>
                <div className="card">
                  <div className="label">Records</div>
                  <div className="chip">{stats.record_count}</div>
                </div>
                <button
                  className="btn secondary"
                  onClick={() => queryClient.invalidateQueries({ queryKey: ["stats", auth.username] })}
                >
                  Refresh
                </button>
              </div>
            )}
          </div>

          <div className="panel">
            <div className="section-title">
              <h2>Edit selected</h2>
              <span className="badge">Inline</span>
            </div>
            {editingId ? (
              <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12 }}>
                <div>
                  <label className="label">Steps</label>
                  <input
                    className="input"
                    value={form.steps}
                    onChange={(e) => setForm((f) => ({ ...f, steps: e.target.value }))}
                    type="number"
                    min={0}
                  />
                </div>
                <div>
                  <label className="label">Sleep</label>
                  <input
                    className="input"
                    value={form.sleep_hours}
                    onChange={(e) => setForm((f) => ({ ...f, sleep_hours: e.target.value }))}
                    type="number"
                    step="0.1"
                    min={0}
                  />
                </div>
                <div>
                  <label className="label">Weight</label>
                  <input
                    className="input"
                    value={form.weight}
                    onChange={(e) => setForm((f) => ({ ...f, weight: e.target.value }))}
                    type="number"
                    step="0.1"
                    min={0}
                  />
                </div>
                <div className="actions">
                  <button className="btn" onClick={saveEdit} disabled={updateMutation.isPending}>
                    {updateMutation.isPending ? "Saving..." : "Save"}
                  </button>
                  <button className="btn secondary" onClick={() => setEditingId(null)}>
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="empty">Select a record to edit.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
