/**
 * Notification Service API Client
 *
 * Encapsulates HTTP calls to `/notifications` endpoints.
 */

import api from "./api";
import type { Notification, NotificationUnreadCount, PipelineRunResult } from "../types/notification";

/**
 * Fetch candidate in-app notifications.
 */
export async function fetchNotifications(limit = 50): Promise<Notification[]> {
  const response = await api.get<Notification[]>("/notifications", {
    params: { limit },
  });
  return response.data;
}

/**
 * Fetch total unread notifications count for badge counter.
 */
export async function fetchUnreadCount(): Promise<number> {
  const response = await api.get<NotificationUnreadCount>("/notifications/unread-count");
  return response.data.unread_count;
}

/**
 * Mark a single notification as read.
 */
export async function markNotificationRead(notificationId: string): Promise<Notification> {
  const response = await api.patch<Notification>(`/notifications/${notificationId}/read`);
  return response.data;
}

/**
 * Mark all candidate notifications as read.
 */
export async function markAllNotificationsRead(): Promise<void> {
  await api.post("/notifications/read-all");
}

/**
 * Trigger the Job Notification Pipeline manually.
 */
export async function runNotificationPipeline(): Promise<PipelineRunResult> {
  const response = await api.post<PipelineRunResult>("/notifications/run-pipeline");
  return response.data;
}

/**
 * Delete a notification entry.
 */
export async function deleteNotification(notificationId: string): Promise<void> {
  await api.delete(`/notifications/${notificationId}`);
}
