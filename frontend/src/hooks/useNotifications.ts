/**
 * React Query Hooks for Notifications
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchNotifications,
  fetchUnreadCount,
  markNotificationRead,
  markAllNotificationsRead,
  runNotificationPipeline,
  deleteNotification,
} from "../services/notificationService";
import { useAuth } from "../contexts/AuthContext";

export function useNotifications(limit = 50) {
  const { token, isLoading: isAuthLoading } = useAuth();

  return useQuery({
    queryKey: ["notifications", limit],
    queryFn: () => fetchNotifications(limit),
    enabled: Boolean(token) && !isAuthLoading,
    staleTime: 1000 * 30, // 30 seconds
    refetchInterval: 1000 * 60, // Poll every minute
  });
}

export function useUnreadCount() {
  const { token, isLoading: isAuthLoading } = useAuth();

  return useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: fetchUnreadCount,
    enabled: Boolean(token) && !isAuthLoading,
    staleTime: 1000 * 30,
    refetchInterval: 1000 * 60,
  });
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (notificationId: string) => markNotificationRead(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

export function useRunNotificationPipeline() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: runNotificationPipeline,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

export function useDeleteNotification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (notificationId: string) => deleteNotification(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}
