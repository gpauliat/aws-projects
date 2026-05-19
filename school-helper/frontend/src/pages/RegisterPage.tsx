import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { signUp, confirmSignUp, signIn } from "../services/auth";

const PASSWORD_RULES = [
  { test: (p: string) => p.length >= 8, label: "At least 8 characters" },
  { test: (p: string) => /[A-Z]/.test(p), label: "One uppercase letter" },
  { test: (p: string) => /[a-z]/.test(p), label: "One lowercase letter" },
  { test: (p: string) => /\d/.test(p), label: "One number" },
];

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
    justifyContent: "center",
    marginTop: "1rem",
    fontSize: "0.875rem",
  },
  link: {
    color: "#4f46e5",
    textDecoration: "none",
  },
  ruleList: {
    listStyle: "none",
    padding: 0,
    margin: "0.25rem 0 0 0",
    fontSize: "0.75rem",
  },
  rulePass: {
    color: "#16a34a",
  },
  ruleFail: {
    color: "#9ca3af",
  },
};

export default function RegisterPage() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Confirmation code step
  const [needsConfirmation, setNeedsConfirmation] = useState(false);
  const [confirmationCode, setConfirmationCode] = useState("");

  function validatePassword(): string | null {
    for (const rule of PASSWORD_RULES) {
      if (!rule.test(password)) {
        return `Password must contain: ${rule.label.toLowerCase()}`;
      }
    }
    if (password !== confirmPassword) {
      return "Passwords do not match.";
    }
    return null;
  }

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    const validationError = validatePassword();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    try {
      const result = await signUp(email, password);
      if (result.nextStep?.signUpStep === "CONFIRM_SIGN_UP") {
        setNeedsConfirmation(true);
      } else {
        // Auto sign-in and redirect
        await signIn(email, password);
        navigate("/dashboard");
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "An unexpected error occurred.";
      setError(message);
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
              Confirmation Code
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
              {loading ? "Confirming…" : "Confirm"}
            </button>
          </form>

          <div style={styles.links}>
            <Link to="/login" style={styles.link}>
              Back to login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>Create Account</h1>

        {error && (
          <div style={styles.error} role="alert">
            {error}
          </div>
        )}

        <form onSubmit={handleRegister} style={styles.form}>
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
              autoComplete="new-password"
              style={styles.input}
            />
            <ul style={styles.ruleList}>
              {PASSWORD_RULES.map((rule) => (
                <li
                  key={rule.label}
                  style={rule.test(password) ? styles.rulePass : styles.ruleFail}
                >
                  {rule.test(password) ? "✓" : "○"} {rule.label}
                </li>
              ))}
            </ul>
          </label>

          <label style={styles.label}>
            Confirm Password
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
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
            {loading ? "Creating account…" : "Create Account"}
          </button>
        </form>

        <div style={styles.links}>
          <Link to="/login" style={styles.link}>
            Already have an account? Log in
          </Link>
        </div>
      </div>
    </div>
  );
}
