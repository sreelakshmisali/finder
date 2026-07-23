/**
 * Profile Setup Type Definitions
 */

import type { Preference } from "./preference";

export interface ResumeSummary {
  has_resume: boolean;
  filename?: string | null;
  full_name?: string | null;
  email?: string | null;
  phone?: string | null;
  skills: string[];
  roles: string[];
  experience: Record<string, unknown>[];
  uploaded_at?: string | null;
}

export interface ProfileSetupData {
  resume_completed: boolean;
  preferences_completed: boolean;
  profile_completion_percentage: number;
  resume_summary?: ResumeSummary | null;
  preferences?: Preference | null;
}
