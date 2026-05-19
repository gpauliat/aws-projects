import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listPdfs, listQuizzes, deletePdf, deleteQuiz, generateQuiz, getPdfProgress } from "../services/api";
import type { PDF, Quiz, PdfProgressResponse } from "../types";
import PdfUploader from "../components/PdfUploader";

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
  },
  title: {
    fontSize: "1.75rem",
    color: "#333",
    margin: 0,
  },
  nav: {
    display: "flex",
    gap: "1rem",
    alignItems: "center",
  },
  navLink: {
    color: "#4f46e5",
    textDecoration: "none",
    fontSize: "0.875rem",
    fontWeight: 500,
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "1.5rem",
    maxWidth: "1200px",
    margin: "0 auto",
  },
  section: {
    backgroundColor: "#fff",
    borderRadius: "8px",
    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
    padding: "1.5rem",
  },
  fullWidth: {
    gridColumn: "1 / -1",
  },
  sectionTitle: {
    fontSize: "1.125rem",
    color: "#333",
    marginTop: 0,
    marginBottom: "1rem",
    borderBottom: "1px solid #eee",
    paddingBottom: "0.5rem",
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
  badge: {
    display: "inline-block",
    padding: "0.2rem 0.5rem",
    borderRadius: "12px",
    fontSize: "0.75rem",
    fontWeight: 600,
    textTransform: "capitalize" as const,
  },
  badgeCompleted: {
    backgroundColor: "#d1fae5",
    color: "#065f46",
  },
  badgePending: {
    backgroundColor: "#fef3c7",
    color: "#92400e",
  },
  badgeProcessing: {
    backgroundColor: "#dbeafe",
    color: "#1e40af",
  },
  badgeFailed: {
    backgroundColor: "#fef2f2",
    color: "#b91c1c",
  },
  btnPrimary: {
    padding: "0.375rem 0.75rem",
    backgroundColor: "#4f46e5",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    fontSize: "0.75rem",
    cursor: "pointer",
    marginRight: "0.5rem",
  },
  btnDanger: {
    padding: "0.375rem 0.75rem",
    backgroundColor: "#dc2626",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    fontSize: "0.75rem",
    cursor: "pointer",
  },
  btnDisabled: {
    padding: "0.375rem 0.75rem",
    backgroundColor: "#a5a3d1",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    fontSize: "0.75rem",
    cursor: "not-allowed",
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
  progressBar: {
    width: "100%",
    height: "8px",
    backgroundColor: "#e5e7eb",
    borderRadius: "4px",
    overflow: "hidden" as const,
  },
  progressFill: {
    height: "100%",
    backgroundColor: "#4f46e5",
    borderRadius: "4px",
    transition: "width 0.3s ease",
  },
  progressRow: {
    display: "flex",
    alignItems: "center",
    gap: "1rem",
    padding: "0.5rem 0",
    borderBottom: "1px solid #f0f0f0",
  },
  progressLabel: {
    flex: "1",
    fontSize: "0.875rem",
    color: "#333",
  },
  progressScore: {
    fontSize: "0.875rem",
    fontWeight: 600,
    color: "#4f46e5",
    minWidth: "60px",
    textAlign: "right" as const,
  },
  progressBarContainer: {
    flex: "1",
    maxWidth: "200px",
  },
  link: {
    color: "#4f46e5",
    textDecoration: "none",
    fontSize: "0.75rem",
    marginRight: "0.5rem",
  },
  actions: {
    display: "flex",
    alignItems: "center",
    gap: "0.25rem",
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

function getStatusBadgeStyle(status: string): React.CSSProperties {
  switch (status) {
    case "completed":
    case "ready":
      return { ...styles.badge, ...styles.badgeCompleted };
    case "pending":
      return { ...styles.badge, ...styles.badgePending };
    case "processing":
    case "syncing":
      return { ...styles.badge, ...styles.badgeProcessing };
    case "failed":
      return { ...styles.badge, ...styles.badgeFailed };
    default:
      return styles.badge;
  }
}

export default function DashboardPage() {
  const [pdfs, setPdfs] = useState<PDF[]>([]);
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [progress, setProgress] = useState<PdfProgressResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [generatingPdfId, setGeneratingPdfId] = useState<string | null>(null);
  const [deletingPdfId, setDeletingPdfId] = useState<string | null>(null);
  const [deletingQuizId, setDeletingQuizId] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  async function loadDashboardData() {
    setLoading(true);
    setError("");
    try {
      const [pdfList, quizList] = await Promise.all([
        listPdfs(),
        listQuizzes(),
      ]);
      setPdfs(pdfList);
      setQuizzes(quizList);

      // Fetch progress for PDFs that have quizzes
      const pdfsWithQuizzes = pdfList.filter((p) => p.quizCount > 0);
      const progressResults = await Promise.all(
        pdfsWithQuizzes.map((p) =>
          getPdfProgress(p.pdfId).catch(() => null)
        )
      );
      setProgress(
        progressResults.filter(
          (r): r is PdfProgressResponse => r !== null && r.totalAttempts > 0
        )
      );
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to load dashboard data.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateQuiz(pdfId: string) {
    setGeneratingPdfId(pdfId);
    setError("");
    try {
      await generateQuiz(pdfId);
      await loadDashboardData();
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to generate quiz.";
      setError(message);
    } finally {
      setGeneratingPdfId(null);
    }
  }

  async function handleDeletePdf(pdfId: string) {
    if (!window.confirm("Delete this PDF and all associated quizzes?")) return;
    setDeletingPdfId(pdfId);
    setError("");
    try {
      await deletePdf(pdfId);
      await loadDashboardData();
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to delete PDF.";
      setError(message);
    } finally {
      setDeletingPdfId(null);
    }
  }

  async function handleDeleteQuiz(quizId: string) {
    if (!window.confirm("Delete this quiz and its history?")) return;
    setDeletingQuizId(quizId);
    setError("");
    try {
      await deleteQuiz(quizId);
      await loadDashboardData();
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to delete quiz.";
      setError(message);
    } finally {
      setDeletingQuizId(null);
    }
  }

  function getPdfName(pdfId: string): string {
    const pdf = pdfs.find((p) => p.pdfId === pdfId);
    return pdf ? pdf.fileName : "Unknown PDF";
  }

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={{ textAlign: "center", padding: "4rem", color: "#888" }}>
          Loading dashboard…
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
        <div style={styles.header}>
          <h1 style={styles.title}>Dashboard</h1>
          <nav style={styles.nav}>
            <Link to="/history" style={styles.navLink}>
              Quiz History
            </Link>
          </nav>
        </div>

        {error && (
          <div style={styles.error} role="alert">
            {error}
          </div>
        )}

        <div style={styles.grid}>
          {/* Upload Section */}
          <div style={{ ...styles.section, ...styles.fullWidth }}>
            <h2 style={styles.sectionTitle}>Upload PDF</h2>
            <PdfUploader onUploadComplete={loadDashboardData} />
          </div>

          {/* Uploaded PDFs Section */}
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>Uploaded PDFs</h2>
            {pdfs.length === 0 ? (
              <div style={styles.emptyState}>
                No PDFs uploaded yet. Upload your first PDF to get started.
              </div>
            ) : (
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>File Name</th>
                    <th style={styles.th}>Uploaded</th>
                    <th style={styles.th}>Status</th>
                    <th style={styles.th}>Quizzes</th>
                    <th style={styles.th}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {pdfs.map((pdf) => (
                    <tr key={pdf.pdfId}>
                      <td style={styles.td}>{pdf.fileName}</td>
                      <td style={styles.td}>{formatDate(pdf.uploadedAt)}</td>
                      <td style={styles.td}>
                        <span style={getStatusBadgeStyle(pdf.extractionStatus)}>
                          {pdf.extractionStatus}
                        </span>
                      </td>
                      <td style={styles.td}>{pdf.quizCount}</td>
                      <td style={styles.td}>
                        <div style={styles.actions}>
                          {(pdf.extractionStatus === "completed" || pdf.extractionStatus === "ready") && (
                            <button
                              style={
                                generatingPdfId === pdf.pdfId
                                  ? styles.btnDisabled
                                  : styles.btnPrimary
                              }
                              disabled={generatingPdfId === pdf.pdfId}
                              onClick={() => handleGenerateQuiz(pdf.pdfId)}
                            >
                              {generatingPdfId === pdf.pdfId
                                ? "Generating…"
                                : "Generate Quiz"}
                            </button>
                          )}
                          <button
                            style={
                              deletingPdfId === pdf.pdfId
                                ? styles.btnDisabled
                                : styles.btnDanger
                            }
                            disabled={deletingPdfId === pdf.pdfId}
                            onClick={() => handleDeletePdf(pdf.pdfId)}
                          >
                            {deletingPdfId === pdf.pdfId
                              ? "Deleting…"
                              : "Delete"}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Quizzes Section */}
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>Available Quizzes</h2>
            {quizzes.length === 0 ? (
              <div style={styles.emptyState}>
                No quizzes yet. Generate a quiz from an uploaded PDF.
              </div>
            ) : (
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>Title</th>
                    <th style={styles.th}>Source PDF</th>
                    <th style={styles.th}>Created</th>
                    <th style={styles.th}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {quizzes.map((quiz) => (
                    <tr key={quiz.quizId}>
                      <td style={styles.td}>{quiz.title}</td>
                      <td style={styles.td}>{getPdfName(quiz.pdfId)}</td>
                      <td style={styles.td}>{formatDate(quiz.createdAt)}</td>
                      <td style={styles.td}>
                        <div style={styles.actions}>
                          <Link
                            to={`/quiz/${quiz.quizId}`}
                            style={styles.link}
                          >
                            Take Quiz
                          </Link>
                          <button
                            style={
                              deletingQuizId === quiz.quizId
                                ? styles.btnDisabled
                                : styles.btnDanger
                            }
                            disabled={deletingQuizId === quiz.quizId}
                            onClick={() => handleDeleteQuiz(quiz.quizId)}
                          >
                            {deletingQuizId === quiz.quizId
                              ? "Deleting…"
                              : "Delete"}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Progress Summary Section */}
          <div style={{ ...styles.section, ...styles.fullWidth }}>
            <h2 style={styles.sectionTitle}>Progress Summary</h2>
            {progress.length === 0 ? (
              <div style={styles.emptyState}>
                No quiz attempts yet. Take a quiz to see your progress.
              </div>
            ) : (
              progress.map((p) => (
                <div key={p.pdfId} style={styles.progressRow}>
                  <span style={styles.progressLabel}>{p.pdfFileName}</span>
                  <div style={styles.progressBarContainer}>
                    <div style={styles.progressBar}>
                      <div
                        style={{
                          ...styles.progressFill,
                          width: `${Math.round(p.averageScore)}%`,
                        }}
                      />
                    </div>
                  </div>
                  <span style={styles.progressScore}>
                    {Math.round(p.averageScore)}%
                  </span>
                  <span
                    style={{
                      fontSize: "0.75rem",
                      color: "#888",
                      minWidth: "80px",
                    }}
                  >
                    {p.totalAttempts} attempt{p.totalAttempts !== 1 ? "s" : ""}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
