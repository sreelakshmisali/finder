/**
 * React Query Hooks for Application & Automation Operations
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchApplications,
  fetchApplicationById,
  createApplication,
  updateApplicationStatus,
  updateApplicationNotes,
  startAutomation,
  confirmSubmit,
} from "../services/applicationService";
import type { ApplicationCreatePayload } from "../types/application";

/**
 * Custom hook to fetch tracked applications list.
 */
export function useApplications(statusFilter?: string) {
  return useQuery({
    queryKey: ["applications", statusFilter],
    queryFn: () => fetchApplications(statusFilter),
  });
}

/**
 * Custom hook to fetch single application by ID.
 */
export function useApplication(id: string, enabled = true) {
  return useQuery({
    queryKey: ["applications", id],
    queryFn: () => fetchApplicationById(id),
    enabled: Boolean(id) && enabled,
  });
}

/**
 * Custom hook to bookmark or save an application.
 */
export function useCreateApplication() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ApplicationCreatePayload) => createApplication(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

/**
 * Custom hook to update application status.
 */
export function useUpdateApplicationStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, status, details }: { id: string; status: string; details?: string }) =>
      updateApplicationStatus(id, status, details),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

/**
 * Custom hook to update application notes.
 */
export function useUpdateApplicationNotes() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, notes }: { id: string; notes: string }) =>
      updateApplicationNotes(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
  });
}

/**
 * Custom hook to start Playwright form automation.
 */
export function useStartAutomation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ applicationId, answers }: { applicationId: string; answers?: Record<string, string> }) =>
      startAutomation(applicationId, answers),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
  });
}

/**
 * Custom hook to confirm and submit final application.
 */
export function useConfirmSubmit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ applicationId, answers }: { applicationId: string; answers?: Record<string, string> }) =>
      confirmSubmit(applicationId, answers),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
