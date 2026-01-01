import { useNavigate } from "@tanstack/react-router";
import { FormEvent, useState } from "react";
import { registerUser } from "../api/auth";

export function Register() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);
    try {
      await registerUser({ username, password });
      setSuccess("Account created. You can sign in now.");
      setTimeout(() => navigate({ to: "/login" }), 800);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="hero">
      <h1>Create account</h1>
      <p className="status">Register to start tracking.</p>
      <form className="panel" style={{ marginTop: 18, maxWidth: 480 }} onSubmit={onSubmit}>
        <label className="label" htmlFor="username">Username</label>
        <input
          id="username"
          className="input"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <label className="label" htmlFor="password" style={{ marginTop: 12 }}>Password</label>
        <input
          id="password"
          className="input"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {error && <div className="status" style={{ color: "var(--danger)", marginTop: 10 }}>{error}</div>}
        {success && <div className="status" style={{ color: "var(--accent)", marginTop: 10 }}>{success}</div>}
        <button className="btn" style={{ marginTop: 14 }} disabled={loading}>
          {loading ? "Creating..." : "Create account"}
        </button>
      </form>
    </div>
  );
}
