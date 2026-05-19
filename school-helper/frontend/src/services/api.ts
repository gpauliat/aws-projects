import { fetchAuthSession } from "aws-amplify/auth";
import type {
  PDF,
  Quiz,
  QuizAttempt,
  UploadResponse,
  QuizSubmitResponse,
  HistoryEntry,
  PdfProgressResponse,
} from "../types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, "") ?? "";

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function getAuthToken(): Promise<string> {
  try {
    const session = await fetchAuthSession();
    const token = session.tokens?.idToken?.toString();
    if (!token) {
      throw new Error("No authentication token available");
    }
    return token;
  } catch {
    throw new ApiError(
      "Your session has expired. Please log in again.",
      401
    );
  }
}

function userFriendlyMessage(status: number, body: string): string {
  if (status === 401) {
    return "Your session has expired. Please log in again.";
  }
  if (status === 403) {
    return "You don't have permission to access this resource.";
  }
  if (status === 404) {
    return "The requested resource was not found.";
  }

  // Try to extract a message from the response body without leaking internals
  try {
    const parsed = JSON.parse(body);
    if (typeof parsed.error === "string" && parsed.error.length > 0) {
      return parsed.error;
    }
    if (typeof parsed.message === "string" && parsed.message.length > 0) {
      return parsed.message;
    }
  } catch {
    // body is not JSON — fall through
  }

  if (status >= 400 && status < 500) {
    return "The request could not be processed. Please check your input and try again.";
  }

  return "An unexpected error occurred. Please try again later.";
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getAuthToken();

  const headers: Record<string, string> = {
    Authorization: token,
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  const responseText = await response.text();

  if (!response.ok) {
    throw new ApiError(
      userFriendlyMessage(response.status, responseText),
      response.status
    );
  }

  if (!responseText) {
    return undefined as unknown as T;
  }

  return JSON.parse(responseText) as T;
}

// ─── PDF Endpoints ───────────────────────────────────────────────────────────

export async function getUploadUrl(
  fileName: string,
  contentType: string,
  fileSize: number
): Promise<UploadResponse> {
  return request<UploadResponse>("/pdfs/upload-url", {
    method: "POST",
    body: JSON.stringify({ fileName, contentType, fileSize }),
  });
}

export async function listPdfs(): Promise<PDF[]> {
  const data = await request<{ pdfs: PDF[] }>("/pdfs");
  return data.pdfs;
}

export async function deletePdf(pdfId: string): Promise<void> {
  return request<void>(`/pdfs/${encodeURIComponent(pdfId)}`, {
    method: "DELETE",
  });
}

// ─── Quiz Generation ─────────────────────────────────────────────────────────

export async function generateQuiz(pdfId: string): Promise<Quiz> {
  return request<Quiz>(
    `/pdfs/${encodeURIComponent(pdfId)}/generate-quiz`,
    { method: "POST" }
  );
}

// ─── Quiz Taking ─────────────────────────────────────────────────────────────

export async function listQuizzes(): Promise<Quiz[]> {
  const data = await request<{ quizzes: Quiz[] }>("/quizzes");
  return data.quizzes;
}

export async function getQuiz(quizId: string): Promise<Quiz> {
  return request<Quiz>(`/quizzes/${encodeURIComponent(quizId)}`);
}

export async function submitQuiz(
  quizId: string,
  answers: { questionId: string; selectedOptionIndex: number }[]
): Promise<QuizSubmitResponse> {
  return request<QuizSubmitResponse>(
    `/quizzes/${encodeURIComponent(quizId)}/submit`,
    {
      method: "POST",
      body: JSON.stringify({ answers }),
    }
  );
}

export async function deleteQuiz(quizId: string): Promise<void> {
  return request<void>(`/quizzes/${encodeURIComponent(quizId)}`, {
    method: "DELETE",
  });
}

// ─── History & Progress ──────────────────────────────────────────────────────

export async function getHistory(): Promise<HistoryEntry[]> {
  return request<HistoryEntry[]>("/history");
}

export async function getAttemptDetail(
  attemptId: string
): Promise<QuizAttempt> {
  return request<QuizAttempt>(
    `/history/${encodeURIComponent(attemptId)}`
  );
}

export async function getPdfProgress(
  pdfId: string
): Promise<PdfProgressResponse> {
  return request<PdfProgressResponse>(
    `/progress/pdf/${encodeURIComponent(pdfId)}`
  );
}

export { ApiError };
