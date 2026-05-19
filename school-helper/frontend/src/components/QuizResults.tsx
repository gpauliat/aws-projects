import React from "react";
import { Link } from "react-router-dom";
import type { QuizSubmitResponse, QuizResult } from "../types";

export interface QuizResultsProps {
  results: QuizSubmitResponse;
  onRetake: () => void;
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: "100vh",
    backgroundColor: "#f5f5f5",
    padding: "2rem",
  },
  card: {
    backgroundColor: "#fff",
    padding: "2rem",
    borderRadius: "8px",
    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
    maxWidth: "700px",
    margin: "0 auto",
  },
  scoreCard: {
    textAlign: "center" as const,
    marginBottom: "2rem",
  },
  scoreValue: {
    fontSize: "3rem",
    fontWeight: 700,
    color: "#4f46e5",
    margin: 0,
  },
  scoreLabel: {
    fontSize: "0.875rem",
    color: "#888",
    marginTop: "0.25rem",
  },
  sectionTitle: {
    fontSize: "1.25rem",
    color: "#333",
    marginTop: 0,
    marginBottom: "1rem",
  },
  resultItem: {
    padding: "1rem",
    marginBottom: "0.75rem",
    borderRadius: "6px",
    border: "1px solid #e5e7eb",
  },
  resultCorrect: {
    backgroundColor: "#f0fdf4",
    borderColor: "#bbf7d0",
  },
  resultIncorrect: {
    backgroundColor: "#fef2f2",
    borderColor: "#fecaca",
  },
  resultPrompt: {
    fontSize: "0.9375rem",
    color: "#333",
    marginBottom: "0.5rem",
    fontWeight: 500,
  },
  resultDetail: {
    fontSize: "0.8125rem",
    color: "#555",
    margin: "0.2rem 0",
  },
  correctAnswer: {
    fontSize: "0.8125rem",
    color: "#065f46",
    fontWeight: 500,
    margin: "0.2rem 0",
  },
  navRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: "2rem",
  },
  backLink: {
    color: "#4f46e5",
    textDecoration: "none",
    fontSize: "0.875rem",
  },
  btnPrimary: {
    padding: "0.75rem 1.5rem",
    backgroundColor: "#4f46e5",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    fontSize: "1rem",
    cursor: "pointer",
  },
};

export default function QuizResults({ results, onRetake }: QuizResultsProps) {
  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.scoreCard}>
          <p style={styles.scoreValue}>{Math.round(results.scorePercent)}%</p>
          <p style={styles.scoreLabel}>
            {results.correctCount} of {results.totalQuestions} correct
          </p>
        </div>

        <h2 style={styles.sectionTitle}>Results</h2>

        {results.results.map((r: QuizResult, idx: number) => (
          <div
            key={r.questionId}
            style={{
              ...styles.resultItem,
              ...(r.isCorrect ? styles.resultCorrect : styles.resultIncorrect),
            }}
          >
            <p style={styles.resultPrompt}>
              {idx + 1}. {r.prompt}
            </p>
            <p style={styles.resultDetail}>
              Your answer: {r.options[r.selectedOptionIndex]}
              {r.isCorrect ? " ✓" : " ✗"}
            </p>
            {!r.isCorrect && (
              <p style={styles.correctAnswer}>
                Correct answer: {r.options[r.correctOptionIndex]}
              </p>
            )}
          </div>
        ))}

        <div style={styles.navRow}>
          <Link to="/dashboard" style={styles.backLink}>
            ← Back to Dashboard
          </Link>
          <button style={styles.btnPrimary} onClick={onRetake}>
            Retake Quiz
          </button>
        </div>
      </div>
    </div>
  );
}
