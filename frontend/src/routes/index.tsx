import { useNavigate } from "@tanstack/react-router";
import { useAuth } from "../state/auth";

export function Home() {
  const { auth } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="hero">
      <h1>Distributed Health Tracking</h1>
      <p>Track health records, see analytics, and watch events flow through services.</p>
      <div className="row" style={{ marginTop: 18 }}>
        <button
          className="btn"
          onClick={() => navigate({ to: auth ? "/app" : "/register" })}
        >
          {auth ? "Go to dashboard" : "Get started"}
        </button>
        {!auth && (
          <button className="btn secondary" onClick={() => navigate({ to: "/login" })}>
            I already have an account
          </button>
        )}
      </div>
      <div style={{ marginTop: 32 }} className="panel">
        <div className="section-title">
          <h2>How it works</h2>
          <span className="badge">API Gateway · FastAPI · RabbitMQ</span>
        </div>
        <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
          <div className="card">
            <h3>Auth</h3>
            <p className="status">Register/login to get a token.</p>
          </div>
          <div className="card">
            <h3>Health Data</h3>
            <p className="status">Send steps, sleep, weight; see list & edits.</p>
          </div>
          <div className="card">
            <h3>Analytics</h3>
            <p className="status">Average steps updates as events stream.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
