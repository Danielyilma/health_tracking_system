import { useNavigate } from "@tanstack/react-router";
import { FormEvent, useState } from "react";
import { loginUser } from "../api/auth";
import { useAuth } from "../state/auth";

export function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await loginUser(username, password);
      login(username, res.access_token);
      navigate({ to: "/app" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="hero">
      <h1>Welcome back</h1>
      <p className="status">Log in to manage your health data.</p>
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
        <button className="btn" style={{ marginTop: 14 }} disabled={loading}>
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </div>
  );
}
