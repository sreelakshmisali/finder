/**
 * React Query Hooks for Saved Searches
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchSavedSearches,
  createSavedSearch,
  runSavedSearch,
  deleteSavedSearch,
} from "../services/savedSearchService";
import type { SavedSearchCreate } from "../types/savedSearch";
import { useAuth } from "../contexts/AuthContext";

export function useSavedSearches() {
  const { token, isLoading: isAuthLoading } = useAuth();

  return useQuery({
    queryKey: ["saved-searches"],
    queryFn: fetchSavedSearches,
    enabled: Boolean(token) && !isAuthLoading,
    staleTime: 1000 * 60 * 5,
  });
}

export function useCreateSavedSearch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: SavedSearchCreate) => createSavedSearch(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["saved-searches"] });
    },
  });
}

export function useRunSavedSearch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (searchId: string) => runSavedSearch(searchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["saved-searches"] });
    },
  });
}

export function useDeleteSavedSearch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (searchId: string) => deleteSavedSearch(searchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["saved-searches"] });
    },
  });
}
