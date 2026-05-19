import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getQuiz, submitQuiz } from "../services/api";
import type { Quiz, QuizSubmitResponse, QuizResult } from "../types";

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
  title: {
    fontSize: "1.5rem",
    color: "#333",
    marginTop: 0,
    marginBottom: "0.5rem",
  },
  subtitle: {
    fontSize: "0.875rem",
    color: "#888",
    marginTop: 0,
    marginBottom: "1.5rem",
  },
  prompt: {
    fontSize: "1.125rem",
    color: "#333",
    marginBottom: "1.25rem",
    lineHeight: 1.5,
  },
  optionButton: {
    display: "block",
    width: "100%",
    padding: "0.875rem 1rem",
    marginBottom: "0.625rem",
    border: "2px solid #e5e7eb",
    borderRadius: "6px",
    backgroundColor: "#fff",
    color: "#333",
    fontSize: "0.9375rem",
    textAlign: "left" as const,
    cursor: "pointer",
    transition: "border-color 0.15s, background-color 0.15s",
  },
  optionSelected: {
    display: "block",
    width: "100%",
    padding: "0.875rem 1rem",
    marginBottom: "0.625rem",
    border: "2px solid #4f46e5",
    borderRadius: "6px",
    backgroundColor: "#eef2ff",
    color: "#333",
    fontSize: "0.9375rem",
    textAlign: "left" as const,
    cursor: "pointer",
  },
  navRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: "1.5rem",
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
  btnDisabled: {
    padding: "0.75rem 1.5rem",
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
    marginBottom: "1rem",
  },
  loading: {
    textAlign: "center" as const,
    padding: "4rem",
    color: "#888",
  },
  // Results styles
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
  backLink: {
    color: "#4f46e5",
    textDecoration: "none",
    fontSize: "0.875rem",
  },
  progressBar: {
    width: "100%",
    height: "6px",
    backgroundColor: "#e5e7eb",
    borderRadius: "3px",
    overflow: "hidden" as const,
    marginBottom: "1.5rem",
  },
  progressFill: {
    height: "100%",
    backgroundColor: "#4f46e5",
    borderRadius: "3px",
    transition: "width 0.3s ease",
  },
};

type QuizState = "loading" | "taking" | "submitting" | "results" | "error";

export default function QuizPage() {
  const { quizId } = useParams<{ quizId: string }>();
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [quizState, setQuizState] = useState<QuizState>("loading");
  const [error, setError] = useState("");
  const [results, setResults] = useState<QuizSubmitResponse | null>(null);

  useEffect(() => {
    if (!quizId) {
      setError("No quiz ID provided.");
      setQuizState("error");
      return;
    }

    let cancelled = false;

    async function loadQuiz() {
      try {
        const data = await getQuiz(quizId!);
        if (!cancelled) {
          setQuiz(data);
          setQuizState("taking");
        }
      } catch (err: unknown) {
        if (!cancelled) {
          const message =
            err instanceof Error ? err.message : "Failed to load quiz.";
          setError(message);
          setQuizState("error");
        }
      }
    }

    loadQuiz();
    return () => {
      cancelled = true;
    };
  }, [quizId]);

  function handleSelectOption(questionId: string, optionIndex: number) {
    setAnswers((prev) => ({ ...prev, [questionId]: optionIndex }));
  }

  function handleNext() {
    if (quiz && currentIndex < quiz.questions.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    }
  }

  async function handleSubmit() {
    if (!quiz || !quizId) return;

    setQuizState("submitting");
    setError("");

    const answerPayload = quiz.questions.map((q) => ({
      questionId: q.questionId,
      selectedOptionIndex: answers[q.questionId] ?? 0,
    }));

    try {
      const response = await submitQuiz(quizId, answerPayload);
      setResults(response);
      setQuizState("results");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to submit quiz.";
      setError(message);
      setQuizState("taking");
    }
  }

  if (quizState === "loading") {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading quiz…</div>
      </div>
    );
  }

  if (quizState === "error") {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <div style={styles.error} role="alert">
            {error}
          </div>
          <Link to="/dashboard" style={styles.backLink}>
            ← Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  if (quizState === "results" && results) {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <div style={styles.scoreCard}>
            <p style={styles.scoreValue}>{Math.round(results.scorePercent)}%</p>
            <p style={styles.scoreLabel}>
              {results.correctCount} of {results.totalQuestions} correct
            </p>
          </div>

          <h2 style={{ ...styles.title, fontSize: "1.25rem", marginBottom: "1rem" }}>
            Results
          </h2>

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
                <p style={{ ...styles.resultDetail, color: "#065f46", fontWeight: 500 }}>
                  Correct answer: {r.options[r.correctOptionIndex]}
                </p>
              )}
            </div>
          ))}

          <div style={{ ...styles.navRow, marginTop: "2rem" }}>
            <Link to="/dashboard" style={styles.backLink}>
              ← Back to Dashboard
            </Link>
            <button
              style={styles.btnPrimary}
              onClick={() => {
                setAnswers({});
                setCurrentIndex(0);
                setResults(null);
                setQuizState("taking");
              }}
            >
              Retake Quiz
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Quiz taking state
  if (!quiz) return null;

  const question = quiz.questions[currentIndex];
  const totalQuestions = quiz.questions.length;
  const isLastQuestion = currentIndex === totalQuestions - 1;
  const hasAnswered = answers[question.questionId] !== undefined;
  const progressPercent = ((currentIndex + 1) / totalQuestions) * 100;

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>{quiz.title}</h1>
        <p style={styles.subtitle}>
          Question {currentIndex + 1} of {totalQuestions}
        </p>

        <div style={styles.progressBar}>
          <div
            style={{ ...styles.progressFill, width: `${progressPercent}%` }}
          />
        </div>

        {error && (
          <div style={styles.error} role="alert">
            {error}
          </div>
        )}

        <p style={styles.prompt}>{question.prompt}</p>

        <div role="radiogroup" aria-label={`Options for question ${currentIndex + 1}`}>
          {question.options.map((option, idx) => {
            const isSelected = answers[question.questionId] === idx;
            return (
              <button
                key={idx}
                type="button"
                role="radio"
                aria-checked={isSelected}
                style={isSelected ? styles.optionSelected : styles.optionButton}
                onClick={() => handleSelectOption(question.questionId, idx)}
              >
                {option}
              </button>
            );
          })}
        </div>

        <div style={styles.navRow}>
          <Link to="/dashboard" style={styles.backLink}>
            ← Back to Dashboard
          </Link>

          {isLastQuestion ? (
            <button
              style={
                !hasAnswered || quizState === "submitting"
                  ? styles.btnDisabled
                  : styles.btnPrimary
              }
              disabled={!hasAnswered || quizState === "submitting"}
              onClick={handleSubmit}
            >
              {quizState === "submitting" ? "Submitting…" : "Submit"}
            </button>
          ) : (
            <button
              style={!hasAnswered ? styles.btnDisabled : styles.btnPrimary}
              disabled={!hasAnswered}
              onClick={handleNext}
            >
              Next
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
