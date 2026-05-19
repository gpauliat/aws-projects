import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getHistory } from "../services/api";
import type { HistoryEntry } from "../types";

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: "100vh",
    backgroundColor: "#f5f5f5",
    padding: "2rem",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "2rem",
    maxWidth: "900px",
    margin: "0 auto 2rem",
  },
  title: {
    fontSize: "1.75rem",
    color: "#333",
    margin: 0,
  },
  backLink: {
    color: "#4f46e5",
    textDecoration: "none",
    fontSize: "0.875rem",
  },
  card: {
    backgroundColor: "#fff",
    borderRadius: "8px",
    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
    padding: "1.5rem",
    maxWidth: "900px",
    margin: "0 auto",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse" as const,
    fontSize: "0.875rem",
  },
  th: {
    textAlign: "left" as const,
    padding: "0.5rem 0.75rem",
    borderBottom: "2px solid #eee",
    color: "#555",
    fontWeight: 600,
  },
  td: {
    padding: "0.5rem 0.75rem",
    borderBottom: "1px solid #f0f0f0",
    color: "#333",
  },
  rowLink: {
    color: "#4f46e5",
    textDecoration: "none",
    fontWeight: 500,
  },
  emptyState: {
    textAlign: "center" as const,
    padding: "2rem",
    color: "#888",
    fontSize: "0.875rem",
  },
  error: {
    backgroundColor: "#fef2f2",
    color: "#b91c1c",
    padding: "0.75rem",
    borderRadius: "4px",
    fontSize: "0.875rem",
    textAlign: "center" as const,
    marginBottom: "1rem",
  },
  loading: {
    textAlign: "center" as const,
    padding: "4rem",
    color: "#888",
  },
  scoreBadge: {
    display: "inline-block",
    padding: "0.2rem 0.5rem",
    borderRadius: "12px",
    fontSize: "0.75rem",
    fontWeight: 600,
  },
};

function formatDate(isoString: string): string {
  try {
    return new Date(isoString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return isoString;
  }
}

function getScoreBadgeStyle(score: number): React.CSSProperties {
  if (score >= 80) {
    return { ...styles.scoreBadge, backgroundColor: "#d1fae5", color: "#065f46" };
  }
  if (score >= 50) {
    return { ...styles.scoreBadge, backgroundColor: "#fef3c7", color: "#92400e" };
  }
  return { ...styles.scoreBadge, backgroundColor: "#fef2f2", color: "#b91c1c" };
}

export default function HistoryPage() {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadHistory() {
      setLoading(true);
      setError("");
      try {
        const data = await getHistory();
        if (!cancelled) {
          setHistory(data);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          const message =
            err instanceof Error ? err.message : "Failed to load quiz history.";
          setError(message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadHistory();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading quiz history…</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>Quiz History</h1>
        <Link to="/dashboard" style={styles.backLink}>
          ← Back to Dashboard
        </Link>
      </div>

      {error && (
        <div style={{ ...styles.error, maxWidth: "900px", margin: "0 auto 1rem" }} role="alert">
          {error}
        </div>
      )}

      <div style={styles.card}>
        {history.length === 0 ? (
          <div style={styles.emptyState}>
            No quiz attempts yet. Take a quiz from the Dashboard to see your history here.
          </div>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Date</th>
                <th style={styles.th}>Source PDF</th>
                <th style={styles.th}>Score</th>
                <th style={styles.th}>Correct / Total</th>
                <th style={styles.th}>Details</th>
              </tr>
            </thead>
            <tbody>
              {history.map((entry) => (
                <tr key={entry.attemptId}>
                  <td style={styles.td}>{formatDate(entry.completedAt)}</td>
                  <td style={styles.td}>{entry.pdfFileName}</td>
                  <td style={styles.td}>
                    <span style={getScoreBadgeStyle(entry.scorePercent)}>
                      {Math.round(entry.scorePercent)}%
                    </span>
                  </td>
                  <td style={styles.td}>
                    {entry.correctCount} / {entry.totalQuestions}
                  </td>
                  <td style={styles.td}>
                    <Link
                      to={`/history/${entry.attemptId}`}
                      style={styles.rowLink}
                    >
                      View Details
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
