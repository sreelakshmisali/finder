/**
 * React Query Hooks for Job Operations
 *
 * Provides custom hooks for fetching job search results, provider lists, and executing AI matching.
 */

import { useQuery, useMutation } from "@tanstack/react-query";
import { searchJobs, fetchProviders, matchJob, fetchSuggestedQueries } from "../services/jobService";
import type { JobSearchQueryParams } from "../types/job";
import { useAuth } from "../contexts/AuthContext";

/**
 * Custom hook to execute a job search with React Query.
 */
export function useJobSearch(params: JobSearchQueryParams, enabled = true) {
  return useQuery({
    queryKey: ["jobs", "search", params],
    queryFn: () => searchJobs(params),
    enabled,
    staleTime: 1000 * 60 * 20, // 20 minutes (aligned with backend TTL)
  });
}

/**
 * Custom hook to fetch list of active job providers.
 */
export function useProviders() {
  return useQuery({
    queryKey: ["jobs", "providers"],
    queryFn: fetchProviders,
    staleTime: 1000 * 60 * 30, // Cache for 30 minutes
  });
}

/**
 * Custom hook to fetch suggested queries generated from active resume and preferences.
 */
export function useSuggestedQueries() {
  const { token, isLoading: isAuthLoading } = useAuth();

  return useQuery({
    queryKey: ["jobs", "suggested-queries"],
    queryFn: fetchSuggestedQueries,
    enabled: Boolean(token) && !isAuthLoading,
    staleTime: 1000 * 60 * 5,
  });
}

/**
 * Custom mutation hook to calculate AI match score for a job.
 */
export function useMatchJob() {
  return useMutation({
    mutationFn: ({ jobId, resumeId }: { jobId: string; resumeId?: string }) =>
      matchJob(jobId, resumeId),
  });
}
