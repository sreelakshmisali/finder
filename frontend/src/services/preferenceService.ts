/**
 * Preference Service API Client
 *
 * Calls `/preferences/` endpoints.
 */

import api from "./api";
import type { Preference, PreferenceUpdatePayload } from "../types/preference";

/**
 * Fetch user preferences.
 */
export async function fetchPreferences(): Promise<Preference> {
  const response = await api.get<Preference>("/preferences/");
  return response.data;
}

/**
 * Save updated user preferences.
 */
export async function savePreferences(payload: PreferenceUpdatePayload): Promise<Preference> {
  const response = await api.put<Preference>("/preferences/", payload);
  return response.data;
}
