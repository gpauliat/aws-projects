import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { resetPassword, confirmPasswordReset } from "../services/auth";

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
  subtitle: {
    textAlign: "center" as const,
    marginBottom: "1rem",
    fontSize: "0.875rem",
    color: "#666",
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
    justifyContent: "center",
    marginTop: "1rem",
    fontSize: "0.875rem",
  },
  link: {
    color: "#4f46e5",
    textDecoration: "none",
  },
};

export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<"request" | "confirm">("request");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleRequestCode(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await resetPassword(email);
      setStep("confirm");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "An unexpected error occurred.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  async function handleConfirmReset(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await confirmPasswordReset(email, code, newPassword);
      navigate("/login");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "An unexpected error occurred.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>Reset Password</h1>

        {step === "request" && (
          <p style={styles.subtitle}>
            Enter your email to receive a verification code.
          </p>
        )}

        {step === "confirm" && (
          <p style={styles.subtitle}>
            Enter the code sent to your email and choose a new password.
          </p>
        )}

        {error && (
          <div style={styles.error} role="alert">
            {error}
          </div>
        )}

        {step === "request" && (
          <form onSubmit={handleRequestCode} style={styles.form}>
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

            <button
              type="submit"
              disabled={loading}
              style={loading ? styles.buttonDisabled : styles.button}
            >
              {loading ? "Sending code…" : "Send Reset Code"}
            </button>
          </form>
        )}

        {step === "confirm" && (
          <form onSubmit={handleConfirmReset} style={styles.form}>
            <label style={styles.label}>
              Verification Code
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                required
                autoComplete="one-time-code"
                style={styles.input}
              />
            </label>

            <label style={styles.label}>
              New Password
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                autoComplete="new-password"
                style={styles.input}
              />
            </label>

            <button
              type="submit"
              disabled={loading}
              style={loading ? styles.buttonDisabled : styles.button}
            >
              {loading ? "Resetting…" : "Reset Password"}
            </button>
          </form>
        )}

        <div style={styles.links}>
          <Link to="/login" style={styles.link}>
            Back to Log In
          </Link>
        </div>
      </div>
    </div>
  );
}
