/**
 * Job Service API Client
 *
 * Encapsulates HTTP calls to `/jobs` endpoints using the configured Axios client.
 */

import api from "./api";
import type { Job, JobListResponse, JobSearchQueryParams, ProviderInfo } from "../types/job";
import type { MatchResult, BatchMatchResult } from "../types/match";

/**
 * Search jobs matching parameters across active providers.
 */
export async function searchJobs(params: JobSearchQueryParams): Promise<JobListResponse> {
  const response = await api.get<JobListResponse>("/jobs/search", {
    params: {
      q: params.query,
      location: params.location,
      remote_only: params.remote_only,
      sources: params.sources,
      manual_search: params.manual_search,
      min_salary: params.min_salary,
      force_refresh: params.force_refresh,
      limit: params.limit || 50,
    },
  });
  return response.data;
}

/**
 * Fetch list of registered job discovery providers.
 */
export async function fetchProviders(): Promise<ProviderInfo[]> {
  const response = await api.get<ProviderInfo[]>("/jobs/providers");
  return response.data;
}

/**
 * Fetch details for a specific job posting by UUID.
 */
export async function fetchJobById(jobId: string): Promise<Job> {
  const response = await api.get<Job>(`/jobs/${jobId}`);
  return response.data;
}

/**
 * Request AI match scoring and explanation for a job.
 */
export async function matchJob(jobId: string, resumeId?: string): Promise<MatchResult> {
  const response = await api.post<MatchResult>("/jobs/match", {
    job_id: jobId,
    resume_id: resumeId,
  });
  return response.data;
}

/**
 * Batch request AI match scores for multiple jobs.
 */
export async function matchBatchJobs(jobIds: string[], resumeId?: string): Promise<BatchMatchResult> {
  const response = await api.post<BatchMatchResult>("/jobs/batch-match", {
    job_ids: jobIds,
    resume_id: resumeId,
  });
  return response.data;
}

/**
 * Fetch candidate-aware suggested search queries generated from active resume and preferences.
 */
export async function fetchSuggestedQueries(): Promise<string[]> {
  const response = await api.get<string[]>("/jobs/suggested-queries");
  return response.data;
}
