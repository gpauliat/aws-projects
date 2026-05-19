import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { signIn, confirmSignUp } from "../services/auth";

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    minHeight: "100vh",
    backgroundColor: "#f5f5f5",
  },
  card: {
    backgroundColor: "#fff",
    padding: "2rem",
    borderRadius: "8px",
    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
    width: "100%",
    maxWidth: "400px",
  },
  title: {
    textAlign: "center" as const,
    marginBottom: "1.5rem",
    fontSize: "1.5rem",
    color: "#333",
  },
  form: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "1rem",
  },
  label: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "0.25rem",
    fontSize: "0.875rem",
    color: "#555",
  },
  input: {
    padding: "0.625rem",
    border: "1px solid #ccc",
    borderRadius: "4px",
    fontSize: "1rem",
  },
  button: {
    padding: "0.75rem",
    backgroundColor: "#4f46e5",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    fontSize: "1rem",
    cursor: "pointer",
  },
  buttonDisabled: {
    padding: "0.75rem",
    backgroundColor: "#a5a3d1",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    fontSize: "1rem",
    cursor: "not-allowed",
  },
  error: {
    backgroundColor: "#fef2f2",
    color: "#b91c1c",
    padding: "0.75rem",
    borderRadius: "4px",
    fontSize: "0.875rem",
    textAlign: "center" as const,
  },
  links: {
    display: "flex",
    justifyContent: "space-between",
    marginTop: "1rem",
    fontSize: "0.875rem",
  },
  link: {
    color: "#4f46e5",
    textDecoration: "none",
  },
};

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Confirmation flow state
  const [needsConfirmation, setNeedsConfirmation] = useState(false);
  const [confirmationCode, setConfirmationCode] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await signIn(email, password);
      navigate("/dashboard");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "An unexpected error occurred.";
      if (message === "USER_NOT_CONFIRMED") {
        setNeedsConfirmation(true);
        setError(
          "Your account has not been confirmed yet. Please enter the verification code sent to your email."
        );
      } else {
        setError(message);
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleConfirm(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await confirmSignUp(email, confirmationCode);
      await signIn(email, password);
      navigate("/dashboard");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "An unexpected error occurred.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  if (needsConfirmation) {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <h1 style={styles.title}>Confirm Your Account</h1>

          {error && (
            <div style={styles.error} role="alert">
              {error}
            </div>
          )}

          <form onSubmit={handleConfirm} style={styles.form}>
            <label style={styles.label}>
              Verification Code
              <input
                type="text"
                value={confirmationCode}
                onChange={(e) => setConfirmationCode(e.target.value)}
                required
                autoComplete="one-time-code"
                style={styles.input}
                placeholder="Enter the code sent to your email"
              />
            </label>

            <button
              type="submit"
              disabled={loading}
              style={loading ? styles.buttonDisabled : styles.button}
            >
              {loading ? "Confirming…" : "Confirm & Log In"}
            </button>
          </form>

          <div style={styles.links}>
            <button
              type="button"
              onClick={() => setNeedsConfirmation(false)}
              style={{ ...styles.link, background: "none", border: "none", cursor: "pointer", padding: 0 }}
            >
              Back to login
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>Log In</h1>

        {error && (
          <div style={styles.error} role="alert">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.label}>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              style={styles.input}
            />
          </label>

          <label style={styles.label}>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              style={styles.input}
            />
          </label>

          <button
            type="submit"
            disabled={loading}
            style={loading ? styles.buttonDisabled : styles.button}
          >
            {loading ? "Logging in…" : "Log In"}
          </button>
        </form>

        <div style={styles.links}>
          <Link to="/register" style={styles.link}>
            Create an account
          </Link>
          <Link to="/reset-password" style={styles.link}>
            Forgot password?
          </Link>
        </div>
      </div>
    </div>
  );
}
