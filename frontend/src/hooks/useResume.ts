/**
 * React Query Hooks for Resume Operations
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchResumes,
  fetchActiveResume,
  uploadResume,
  setActiveResume,
  parseResume,
  deleteResume,
} from "../services/resumeService";

/**
 * Fetch all resumes hook.
 */
export function useResumes() {
  return useQuery({
    queryKey: ["resumes"],
    queryFn: fetchResumes,
  });
}

/**
 * Fetch active resume hook.
 */
export function useActiveResume() {
  return useQuery({
    queryKey: ["resumes", "active"],
    queryFn: fetchActiveResume,
  });
}

/**
 * Upload resume mutation hook.
 */
export function useUploadResume() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => uploadResume(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
      queryClient.invalidateQueries({ queryKey: ["onboarding"] });
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
  });
}

/**
 * Set active resume mutation hook.
 */
export function useSetActiveResume() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (resumeId: string) => setActiveResume(resumeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
      queryClient.invalidateQueries({ queryKey: ["onboarding"] });
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
  });
}

/**
 * Parse resume mutation hook.
 */
export function useParseResume() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (resumeId: string) => parseResume(resumeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
      queryClient.invalidateQueries({ queryKey: ["onboarding"] });
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
  });
}

/**
 * Delete resume mutation hook.
 */
export function useDeleteResume() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (resumeId: string) => deleteResume(resumeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
      queryClient.invalidateQueries({ queryKey: ["onboarding"] });
    },
  });
}

