/**
 * Application Service API Client
 *
 * Calls `/applications` endpoints.
 */

import api from "./api";
import type {
  Application,
  ApplicationListResponse,
  ApplicationCreatePayload,
} from "../types/application";
import type { AutomationStateResponse } from "../types/automation";

/**
 * Bookmark or approve a job application.
 */
export async function createApplication(payload: ApplicationCreatePayload): Promise<Application> {
  const response = await api.post<Application>("/applications/", payload);
  return response.data;
}

/**
 * Fetch tracked applications with optional status filter.
 */
export async function fetchApplications(statusFilter?: string): Promise<ApplicationListResponse> {
  const response = await api.get<ApplicationListResponse>("/applications/", {
    params: { status: statusFilter },
  });
  return response.data;
}

/**
 * Fetch application details by ID.
 */
export async function fetchApplicationById(id: string): Promise<Application> {
  const response = await api.get<Application>(`/applications/${id}`);
  return response.data;
}

/**
 * Update application status.
 */
export async function updateApplicationStatus(
  id: string,
  newStatus: string,
  details?: string
): Promise<Application> {
  const response = await api.patch<Application>(`/applications/${id}/status`, {
    status: newStatus,
    details,
  });
  return response.data;
}

/**
 * Update application notes.
 */
export async function updateApplicationNotes(id: string, notes: string): Promise<Application> {
  const response = await api.patch<Application>(`/applications/${id}/notes`, {
    notes,
  });
  return response.data;
}

/**
 * Start Playwright automation to fill application form and attach resume.
 */
export async function startAutomation(
  applicationId: string,
  answers?: Record<string, string>
): Promise<AutomationStateResponse> {
  const response = await api.post<AutomationStateResponse>(
    `/applications/${applicationId}/start-automation`,
    { answers }
  );
  return response.data;
}

/**
 * Confirm and submit final application after user approval.
 */
export async function confirmSubmit(
  applicationId: string,
  answers: Record<string, string> = {}
): Promise<Application> {
  const response = await api.post<Application>(
    `/applications/${applicationId}/confirm-submit`,
    { answers }
  );
  return response.data;
}
