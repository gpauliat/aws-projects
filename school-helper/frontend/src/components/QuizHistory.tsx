import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getAttemptDetail, getQuiz } from "../services/api";
import type { QuizAttempt, Quiz, Question } from "../types";

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
    maxWidth: "700px",
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
  loading: {
    textAlign: "center" as const,
    padding: "4rem",
    color: "#888",
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
};

export default function QuizHistory() {
  const { attemptId } = useParams<{ attemptId: string }>();
  const [attempt, setAttempt] = useState<QuizAttempt | null>(null);
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadAttemptDetail() {
      if (!attemptId) {
        setError("No attempt ID provided.");
        setLoading(false);
        return;
      }

      setLoading(true);
      setError("");

      try {
        const attemptData = await getAttemptDetail(attemptId);
        if (cancelled) return;
        setAttempt(attemptData);

        const quizData = await getQuiz(attemptData.quizId);
        if (cancelled) return;
        setQuiz(quizData);
      } catch (err: unknown) {
        if (!cancelled) {
          const message =
            err instanceof Error
              ? err.message
              : "Failed to load attempt details.";
          setError(message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadAttemptDetail();
    return () => {
      cancelled = true;
    };
  }, [attemptId]);

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading attempt details…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.container}>
        <div style={{ ...styles.error, maxWidth: "700px", margin: "2rem auto" }} role="alert">
          {error}
        </div>
        <div style={{ textAlign: "center" }}>
          <Link to="/history" style={styles.backLink}>
            ← Back to History
          </Link>
        </div>
      </div>
    );
  }

  if (!attempt || !quiz) {
    return null;
  }

  // Build a map from questionId to Question for quick lookup
  const questionMap = new Map<string, Question>();
  for (const q of quiz.questions) {
    questionMap.set(q.questionId, q);
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>Attempt Details</h1>
        <Link to="/history" style={styles.backLink}>
          ← Back to History
        </Link>
      </div>

      <div style={styles.card}>
        <div style={styles.scoreCard}>
          <p style={styles.scoreValue}>{Math.round(attempt.scorePercent)}%</p>
          <p style={styles.scoreLabel}>
            {attempt.correctCount} of {attempt.totalQuestions} correct
          </p>
        </div>

        <h2 style={styles.sectionTitle}>Questions</h2>

        {attempt.answers.map((answer, idx) => {
          const question = questionMap.get(answer.questionId);
          const userAnswerText =
            question?.options[answer.selectedOptionIndex] ?? `Option ${answer.selectedOptionIndex + 1}`;
          const correctAnswerText =
            question && question.correctOptionIndex != null
              ? question.options[question.correctOptionIndex]
              : undefined;

          return (
            <div
              key={answer.questionId}
              style={{
                ...styles.resultItem,
                ...(answer.isCorrect
                  ? styles.resultCorrect
                  : styles.resultIncorrect),
              }}
            >
              <p style={styles.resultPrompt}>
                {idx + 1}. {question?.prompt ?? "Question not available"}
              </p>
              <p style={styles.resultDetail}>
                Your answer: {userAnswerText}
                {answer.isCorrect ? " ✓" : " ✗"}
              </p>
              {!answer.isCorrect && correctAnswerText && (
                <p style={styles.correctAnswer}>
                  Correct answer: {correctAnswerText}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
