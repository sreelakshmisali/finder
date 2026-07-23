/**
 * Onboarding Service API Client
 *
 * Calls `/onboarding/status` endpoint to check active resume and profile completion metrics.
 */

import api from "./api";
import type { OnboardingStatus } from "../types/onboarding";

/**
 * Fetch candidate onboarding completion status.
 */
export async function fetchOnboardingStatus(): Promise<OnboardingStatus> {
  const response = await api.get<OnboardingStatus>("/onboarding/status");
  return response.data;
}
