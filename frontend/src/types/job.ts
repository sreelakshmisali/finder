/**
 * Job TypeScript Type Definitions
 *
 * Interfaces matching the backend Pydantic schemas for jobs and search parameters.
 */

export type SearchMode = "NORMAL" | "SMART";

export interface Job {
  id: string;
  company: string;
  title: string;
  location: string;
  remote: boolean;
  salary?: string | null;
  description: string;
  url: string;
  source: string;
  apply_url?: string | null;
  can_apply: boolean;
  posted_date: string;
  fetched_at: string;
  content_hash: string;
  /* Optional match score attached when matching service is invoked */
  match_score?: number;
}

export interface JobSearchQueryParams {
  query?: string;
  location?: string;
  remote_only?: boolean;
  search_mode?: SearchMode;
  min_salary?: number;
  force_refresh?: boolean;
  limit?: number;
}

export interface JobListResponse {
  total: number;
  jobs: Job[];
  suggested_queries?: string[];
  search_mode?: SearchMode;
  applied_query?: string;
  applied_location?: string;
}
