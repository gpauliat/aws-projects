// ─── Core Data Models ────────────────────────────────────────────────────────

export interface PDF {
  pdfId: string;
  userId: string;
  fileName: string;
  s3Key: string;
  fileSizeBytes: number;
  uploadedAt: string;
  extractionStatus: 'pending' | 'processing' | 'completed' | 'ready' | 'failed';
  quizCount: number;
}

export interface Question {
  questionId: string;
  prompt: string;
  options: string[]; // exactly 4
  correctOptionIndex?: number; // 0-3, excluded when taking quiz
  difficulty: 'easy' | 'medium' | 'hard';
}

export interface Quiz {
  quizId: string;
  pdfId: string;
  userId: string;
  title: string;
  createdAt: string;
  questions: Question[];
  questionCount?: number; // included in list responses
}

export interface Answer {
  questionId: string;
  selectedOptionIndex: number;
  isCorrect: boolean;
}

export interface QuizAttempt {
  attemptId: string;
  quizId: string;
  userId: string;
  pdfId: string;
  completedAt: string;
  scorePercent: number;
  totalQuestions: number;
  correctCount: number;
  answers: Answer[];
}

// ─── API Response Types ──────────────────────────────────────────────────────

export interface QuizResult {
  questionId: string;
  prompt: string;
  options: string[];
  selectedOptionIndex: number;
  correctOptionIndex: number;
  isCorrect: boolean;
}

export interface UploadResponse {
  pdfId: string;
  uploadUrl: string;
}

export interface QuizSubmitResponse {
  attemptId: string;
  quizId: string;
  scorePercent: number;
  totalQuestions: number;
  correctCount: number;
  completedAt: string;
  results: QuizResult[];
}

export interface HistoryEntry {
  attemptId: string;
  quizId: string;
  pdfId: string;
  pdfFileName: string;
  completedAt: string;
  scorePercent: number;
  totalQuestions: number;
  correctCount: number;
}

export interface PdfProgressResponse {
  pdfId: string;
  pdfFileName: string;
  averageScore: number;
  totalAttempts: number;
}
