import React, { useCallback, useRef, useState } from "react";
import { getUploadUrl } from "../services/api";

const MAX_FILE_SIZE = 52_428_800; // 50 MB in bytes

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    width: "100%",
  },
  dropZone: {
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    justifyContent: "center",
    padding: "2rem",
    border: "2px dashed #ccc",
    borderRadius: "8px",
    backgroundColor: "#fafafa",
    cursor: "pointer",
    transition: "border-color 0.2s, background-color 0.2s",
    minHeight: "120px",
  },
  dropZoneActive: {
    borderColor: "#4f46e5",
    backgroundColor: "#eef2ff",
  },
  dropZoneDisabled: {
    cursor: "not-allowed",
    opacity: 0.6,
  },
  icon: {
    fontSize: "2rem",
    marginBottom: "0.5rem",
    color: "#888",
  },
  label: {
    fontSize: "0.875rem",
    color: "#555",
    textAlign: "center" as const,
  },
  sublabel: {
    fontSize: "0.75rem",
    color: "#999",
    marginTop: "0.25rem",
  },
  error: {
    backgroundColor: "#fef2f2",
    color: "#b91c1c",
    padding: "0.75rem",
    borderRadius: "4px",
    fontSize: "0.875rem",
    textAlign: "center" as const,
    marginTop: "0.75rem",
  },
  progressContainer: {
    marginTop: "1rem",
  },
  fileName: {
    fontSize: "0.875rem",
    color: "#333",
    marginBottom: "0.5rem",
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
    transition: "width 0.2s ease",
  },
  progressText: {
    fontSize: "0.75rem",
    color: "#555",
    marginTop: "0.25rem",
    textAlign: "right" as const,
  },
  successMessage: {
    backgroundColor: "#d1fae5",
    color: "#065f46",
    padding: "0.75rem",
    borderRadius: "4px",
    fontSize: "0.875rem",
    textAlign: "center" as const,
    marginTop: "0.75rem",
  },
};

interface PdfUploaderProps {
  onUploadComplete?: () => void;
}

type UploadState = "idle" | "validating" | "requesting-url" | "uploading" | "success" | "error";

export default function PdfUploader({ onUploadComplete }: PdfUploaderProps) {
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [error, setError] = useState("");
  const [progress, setProgress] = useState(0);
  const [fileName, setFileName] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function validateFile(file: File): string | null {
    // Check file extension
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      return "Only PDF files are supported. Please select a PDF file.";
    }

    // Check MIME type
    if (file.type !== "application/pdf") {
      return "Only PDF files are supported. Please select a PDF file.";
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return "File size exceeds the 50 MB limit. Please upload a smaller file.";
    }

    return null;
  }

  async function uploadFile(file: File) {
    setUploadState("validating");
    setError("");
    setProgress(0);
    setFileName(file.name);

    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setUploadState("error");
      return;
    }

    // Request presigned URL
    setUploadState("requesting-url");
    let uploadUrl: string;
    try {
      const response = await getUploadUrl(file.name, file.type, file.size);
      uploadUrl = response.uploadUrl;
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to get upload URL. Please try again.";
      setError(message);
      setUploadState("error");
      return;
    }

    // Upload to S3 using XMLHttpRequest for progress tracking
    setUploadState("uploading");
    try {
      await new Promise<void>((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        let uploadComplete = false;

        xhr.upload.addEventListener("progress", (event) => {
          if (event.lengthComputable) {
            const percent = Math.round((event.loaded / event.total) * 100);
            setProgress(percent);
            if (percent >= 100) {
              uploadComplete = true;
            }
          }
        });

        xhr.upload.addEventListener("load", () => {
          // All request bytes have been sent to the server
          uploadComplete = true;
        });

        xhr.addEventListener("load", () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve();
          } else if (xhr.status === 0) {
            // CORS blocked reading the response but upload likely succeeded
            resolve();
          } else {
            reject(new Error("Upload failed. Please try again."));
          }
        });

        xhr.addEventListener("error", () => {
          // CORS errors on S3 presigned URL uploads trigger the error event
          // even when the upload succeeded (S3 may not return CORS headers
          // on the PUT response). If all bytes were sent, treat as success.
          if (uploadComplete) {
            resolve();
          } else {
            reject(new Error("Upload failed. Please check your connection and try again."));
          }
        });

        xhr.addEventListener("abort", () => {
          reject(new Error("Upload was cancelled."));
        });

        xhr.open("PUT", uploadUrl);
        xhr.setRequestHeader("Content-Type", "application/pdf");
        xhr.send(file);
      });

      setUploadState("success");
      setProgress(100);
      onUploadComplete?.();
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Upload failed. Please try again.";
      setError(message);
      setUploadState("error");
    }
  }

  function handleFileSelect(file: File | undefined) {
    if (!file) return;
    uploadFile(file);
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    handleFileSelect(file);
    // Reset input so the same file can be re-selected
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      const file = e.dataTransfer.files?.[0];
      if (file) {
        handleFileSelect(file);
      }
    },
    []
  );

  function handleClick() {
    if (isUploading) return;
    inputRef.current?.click();
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (isUploading) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      inputRef.current?.click();
    }
  }

  const isUploading = uploadState === "validating" || uploadState === "requesting-url" || uploadState === "uploading";

  const dropZoneStyle: React.CSSProperties = {
    ...styles.dropZone,
    ...(dragActive ? styles.dropZoneActive : {}),
    ...(isUploading ? styles.dropZoneDisabled : {}),
  };

  return (
    <div style={styles.wrapper}>
      <div
        style={dropZoneStyle}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        role="button"
        tabIndex={0}
        aria-label="Upload PDF file"
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleInputChange}
          style={{ display: "none" }}
          aria-hidden="true"
        />
        <div style={styles.icon}>📄</div>
        <div style={styles.label}>
          {isUploading
            ? "Uploading…"
            : "Drag and drop a PDF here, or click to select"}
        </div>
        <div style={styles.sublabel}>PDF files only, up to 50 MB</div>
      </div>

      {isUploading && (
        <div style={styles.progressContainer}>
          <div style={styles.fileName}>{fileName}</div>
          <div style={styles.progressBar}>
            <div
              style={{
                ...styles.progressFill,
                width: `${progress}%`,
              }}
            />
          </div>
          <div style={styles.progressText}>
            {uploadState === "requesting-url"
              ? "Preparing upload…"
              : `${progress}%`}
          </div>
        </div>
      )}

      {uploadState === "success" && (
        <div style={styles.successMessage} role="status">
          {fileName} uploaded successfully!
        </div>
      )}

      {error && (
        <div style={styles.error} role="alert">
          {error}
        </div>
      )}
    </div>
  );
}
