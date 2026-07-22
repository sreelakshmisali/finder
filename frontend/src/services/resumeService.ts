/**
 * Resume Service API Client
 *
 * Encapsulates HTTP calls to `/resume` endpoints.
 */

import api from "./api";
import type { Resume, ResumeListResponse } from "../types/resume";

/**
 * Upload a PDF file resume using Multipart FormData.
 */
export async function uploadResume(file: File): Promise<Resume> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post<Resume>("/resume/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
}

/**
 * Fetch all uploaded resumes.
 */
export async function fetchResumes(): Promise<ResumeListResponse> {
  const response = await api.get<ResumeListResponse>("/resume/");
  return response.data;
}

/**
 * Fetch currently active resume.
 */
export async function fetchActiveResume(): Promise<Resume | null> {
  const response = await api.get<Resume | null>("/resume/active");
  return response.data;
}

/**
 * Mark a resume as active.
 */
export async function setActiveResume(resumeId: string): Promise<Resume> {
  const response = await api.patch<Resume>(`/resume/${resumeId}/active`);
  return response.data;
}

/**
 * Trigger AI parsing on an uploaded resume.
 */
export async function parseResume(resumeId: string): Promise<Resume> {
  const response = await api.post<Resume>(`/resume/${resumeId}/parse`);
  return response.data;
}

/**
 * Permanently delete an uploaded resume.
 */
export async function deleteResume(resumeId: string): Promise<{ message: string }> {
  const response = await api.delete<{ message: string }>(`/resume/${resumeId}`);
  return response.data;
}

