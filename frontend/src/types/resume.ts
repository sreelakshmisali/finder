/**
 * Resume TypeScript Type Definitions
 */

export interface ParsedResumeData {
  full_name?: string;
  email?: string;
  phone?: string;
  skills: string[];
  experience: Record<string, unknown>[];
  education: Record<string, unknown>[];
  projects: Record<string, unknown>[];
}

export interface Resume {
  id: string;
  filename: string;
  file_path: string;
  raw_text?: string | null;
  parsed_data?: ParsedResumeData | Record<string, unknown> | null;
  is_active: boolean;
  uploaded_at: string;
}

export interface ResumeListResponse {
  total: number;
  resumes: Resume[];
}
