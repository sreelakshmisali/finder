/**
 * Profile Service API Client
 *
 * Calls `/profile/setup` endpoint to fetch combined resume capability + preferences goal status.
 */

import api from "./api";
import type { ProfileSetupData } from "../types/profile";

/**
 * Fetch combined profile setup metrics.
 */
export async function fetchProfileSetup(): Promise<ProfileSetupData> {
  const response = await api.get<ProfileSetupData>("/profile/setup");
  return response.data;
}
