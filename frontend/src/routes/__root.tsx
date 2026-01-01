import { Outlet, useNavigate, Link } from "@tanstack/react-router";
import { useAuth } from "../state/auth";

export function RootLayout() {
  const { auth, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="container">
      <nav className="nav">
        <div className="brand">Health Tracking</div>
        <div>
          <Link to="/" search={{}} className="badge">
            Home
          </Link>
          {auth ? (
            <>
              <Link to="/app" search={{}} style={{ marginLeft: 12 }}>
                Dashboard
              </Link>
              <button
                className="btn secondary"
                style={{ marginLeft: 12 }}
                onClick={() => {
                  logout();
                  navigate({ to: "/login" });
                }}
              >
                Logout ({auth.username})
              </button>
            </>
          ) : (
            <>
              <Link to="/login" search={{}} style={{ marginLeft: 12 }}>
                Login
              </Link>
              <Link to="/register" search={{}} style={{ marginLeft: 12 }}>
                Register
              </Link>
            </>
          )}
        </div>
      </nav>
      <Outlet />
    </div>
  );
}
