/**
 * Application TypeScript Type Definitions
 */

import type { Job } from "./job";

export interface ApplicationLog {
  id: string;
  application_id: string;
  action: string;
  old_status?: string | null;
  new_status: string;
  details?: string | null;
  created_at: string;
}

export interface Application {
  id: string;
  job_id: string;
  status: string;
  match_score?: number | null;
  match_details?: Record<string, unknown> | null;
  notes?: string | null;
  applied_date?: string | null;
  created_at: string;
  updated_at: string;
  job: Job;
  logs: ApplicationLog[];
}

export interface ApplicationListResponse {
  total: number;
  applications: Application[];
}

export interface ApplicationCreatePayload {
  job_id: string;
  status?: string;
  notes?: string;
}
