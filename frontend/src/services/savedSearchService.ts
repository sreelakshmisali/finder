/**
 * Saved Search Service API Client
 *
 * Encapsulates HTTP calls to `/saved-searches` endpoints.
 */

import api from "./api";
import type { SavedSearch, SavedSearchCreate } from "../types/savedSearch";

/**
 * Fetch all saved search rules for the current user.
 */
export async function fetchSavedSearches(): Promise<SavedSearch[]> {
  const response = await api.get<SavedSearch[]>("/saved-searches");
  return response.data;
}

/**
 * Create a new saved search rule.
 */
export async function createSavedSearch(payload: SavedSearchCreate): Promise<SavedSearch> {
  const response = await api.post<SavedSearch>("/saved-searches", payload);
  return response.data;
}

/**
 * Mark saved search rule as executed and update last_run timestamp.
 */
export async function runSavedSearch(searchId: string): Promise<SavedSearch> {
  const response = await api.post<SavedSearch>(`/saved-searches/${searchId}/run`);
  return response.data;
}

/**
 * Permanently delete a saved search rule.
 */
export async function deleteSavedSearch(searchId: string): Promise<void> {
  await api.delete(`/saved-searches/${searchId}`);
}
