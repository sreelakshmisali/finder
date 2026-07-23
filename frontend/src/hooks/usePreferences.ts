/**
 * React Query Hooks for Preference Operations
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchPreferences, savePreferences } from "../services/preferenceService";
import type { PreferenceUpdatePayload } from "../types/preference";

/**
 * Custom hook to fetch preferences.
 */
export function usePreferences() {
  return useQuery({
    queryKey: ["preferences"],
    queryFn: fetchPreferences,
  });
}

/**
 * Custom hook to save updated preferences.
 */
export function useSavePreferences() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: PreferenceUpdatePayload) => savePreferences(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["preferences"] });
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
  });
}
