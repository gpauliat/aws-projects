import React, { useEffect, useState } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  Outlet,
  Link,
  useNavigate,
} from "react-router-dom";
import { getCurrentUser, signOut } from "./services/auth";
import type { AuthUser } from "./services/auth";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import DashboardPage from "./pages/DashboardPage";
import QuizPage from "./pages/QuizPage";
import HistoryPage from "./pages/HistoryPage";
import QuizHistory from "./components/QuizHistory";

// ─── Styles ──────────────────────────────────────────────────────────────────

const layoutStyles: Record<string, React.CSSProperties> = {
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "0.75rem 1.5rem",
    backgroundColor: "#4f46e5",
    color: "#fff",
  },
  brand: {
    fontSize: "1.125rem",
    fontWeight: 600,
    color: "#fff",
    textDecoration: "none",
  },
  nav: {
    display: "flex",
    gap: "1.25rem",
    alignItems: "center",
  },
  navLink: {
    color: "#e0e7ff",
    textDecoration: "none",
    fontSize: "0.875rem",
    fontWeight: 500,
  },
  logoutButton: {
    padding: "0.375rem 0.75rem",
    backgroundColor: "transparent",
    color: "#e0e7ff",
    border: "1px solid #e0e7ff",
    borderRadius: "4px",
    fontSize: "0.8125rem",
    cursor: "pointer",
  },
};

// ─── Auth Context ────────────────────────────────────────────────────────────

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  refreshUser: () => Promise<void>;
}

const AuthContext = React.createContext<AuthContextValue>({
  user: null,
  loading: true,
  refreshUser: async () => {},
});

function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  async function refreshUser() {
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshUser();
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return React.useContext(AuthContext);
}

// ─── Auth Guard ──────────────────────────────────────────────────────────────

function RequireAuth() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: "4rem", color: "#888" }}>
        Loading…
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}

// ─── Shared Layout ───────────────────────────────────────────────────────────

function AppLayout() {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();

  async function handleLogout() {
    try {
      await signOut();
      await refreshUser();
      navigate("/login");
    } catch {
      // Force redirect even if signOut throws
      navigate("/login");
    }
  }

  return (
    <>
      <header style={layoutStyles.header}>
        <Link to="/dashboard" style={layoutStyles.brand}>
          Quiz Generator
        </Link>
        <nav style={layoutStyles.nav}>
          <Link to="/dashboard" style={layoutStyles.navLink}>
            Dashboard
          </Link>
          <Link to="/history" style={layoutStyles.navLink}>
            History
          </Link>
          <button
            onClick={handleLogout}
            style={layoutStyles.logoutButton}
            type="button"
          >
            Logout
          </button>
        </nav>
      </header>
      <Outlet />
    </>
  );
}

// ─── App ─────────────────────────────────────────────────────────────────────

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />

          {/* Protected routes with shared layout */}
          <Route element={<RequireAuth />}>
            <Route element={<AppLayout />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/quiz/:quizId" element={<QuizPage />} />
              <Route path="/history" element={<HistoryPage />} />
              <Route path="/history/:attemptId" element={<QuizHistory />} />
            </Route>
          </Route>

          {/* Default and catch-all routes */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
