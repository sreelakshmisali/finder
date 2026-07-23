/**
 * Job TypeScript Type Definitions
 *
 * Interfaces matching the backend Pydantic schemas for jobs and search parameters.
 */

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
  sources?: string[];
  manual_search?: boolean;
  min_salary?: number;
  force_refresh?: boolean;
  limit?: number;
}

export interface JobListResponse {
  total: number;
  jobs: Job[];
  providers_searched: string[];
  suggested_queries?: string[];
  is_generated?: boolean;
  applied_query?: string;
  applied_location?: string;
}

export interface ProviderInfo {
  name: string;
  display_name: string;
  description: string;
  enabled: boolean;
}
