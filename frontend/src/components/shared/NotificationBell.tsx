/**
 * NotificationBell Component
 *
 * Header bell icon component displaying live unread notification badge
 * and dropdown panel with high-matching job alerts.
 */

import { useState, useRef, useEffect } from "react";
import { Bell, Sparkles, CheckCheck, RefreshCw, Trash2, ExternalLink } from "lucide-react";
import { Badge, Spinner } from "../ui";
import {
  useNotifications,
  useUnreadCount,
  useMarkNotificationRead,
  useMarkAllNotificationsRead,
  useRunNotificationPipeline,
  useDeleteNotification,
} from "../../hooks/useNotifications";
import { useNavigate } from "react-router-dom";

function NotificationBell() {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const { data: notifications = [], isLoading } = useNotifications();
  const { data: unreadCount = 0 } = useUnreadCount();

  const markReadMutation = useMarkNotificationRead();
  const markAllReadMutation = useMarkAllNotificationsRead();
  const runPipelineMutation = useRunNotificationPipeline();
  const deleteNotificationMutation = useDeleteNotification();

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleNotificationClick = (notification: any) => {
    if (!notification.read) {
      markReadMutation.mutate(notification.id);
    }
    setIsOpen(false);
    navigate("/jobs");
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Trigger Icon Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        title="In-app Notifications & Job Alerts"
        className="relative p-2 rounded-xl text-text-secondary hover:text-text hover:bg-surface-elevated transition-all cursor-pointer border border-transparent hover:border-border"
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 h-5 min-w-[20px] px-1 bg-error text-white font-black text-[10px] rounded-full flex items-center justify-center shadow-sm animate-pulse">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {/* Notifications Dropdown Panel */}
      {isOpen && (
        <div className="absolute right-0 mt-3 w-80 sm:w-96 rounded-2xl bg-surface border border-border shadow-xl z-50 overflow-hidden animate-in fade-in duration-200">
          {/* Header */}
          <div className="p-4 border-b border-border bg-surface-elevated/40 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles size={16} className="text-primary" />
              <h3 className="text-sm font-bold text-text">Job Match Alerts</h3>
              {unreadCount > 0 && (
                <Badge variant="primary" className="text-[10px] py-0.5 px-2 font-bold">
                  {unreadCount} New
                </Badge>
              )}
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => runPipelineMutation.mutate()}
                disabled={runPipelineMutation.isPending}
                title="Run Notification Pipeline now"
                className="text-xs text-text-muted hover:text-primary p-1 transition-colors cursor-pointer flex items-center gap-1 font-semibold"
              >
                <RefreshCw size={13} className={runPipelineMutation.isPending ? "animate-spin text-primary" : ""} />
                Check New
              </button>

              {unreadCount > 0 && (
                <button
                  type="button"
                  onClick={() => markAllReadMutation.mutate()}
                  title="Mark all as read"
                  className="text-xs text-primary font-semibold hover:underline flex items-center gap-1 cursor-pointer"
                >
                  <CheckCheck size={14} /> Read All
                </button>
              )}
            </div>
          </div>

          {/* Pipeline Running Banner Notice */}
          {runPipelineMutation.isPending && (
            <div className="p-3 bg-primary/10 border-b border-primary/20 text-xs font-semibold text-primary flex items-center gap-2">
              <Spinner size="sm" />
              <span>Evaluating saved searches & checking high match jobs...</span>
            </div>
          )}

          {/* Pipeline Completed Message */}
          {runPipelineMutation.data && !runPipelineMutation.isPending && (
            <div className="p-3 bg-success/10 border-b border-success/20 text-xs font-semibold text-success flex items-center justify-between">
              <span>{runPipelineMutation.data.message}</span>
            </div>
          )}

          {/* Notifications List Body */}
          <div className="max-h-96 overflow-y-auto divide-y divide-border">
            {isLoading ? (
              <div className="flex justify-center py-8">
                <Spinner size="sm" />
              </div>
            ) : notifications.length === 0 ? (
              <div className="p-8 text-center space-y-2">
                <Bell size={28} className="mx-auto text-text-muted opacity-50" />
                <p className="text-xs font-semibold text-text">No job notifications yet</p>
                <p className="text-[11px] text-text-muted">
                  Saved search pipeline will alert you when high-matching jobs (&ge;75% fit) are discovered.
                </p>
              </div>
            ) : (
              notifications.map((item) => (
                <div
                  key={item.id}
                  onClick={() => handleNotificationClick(item)}
                  className={`p-4 transition-all cursor-pointer hover:bg-surface-elevated/80 flex items-start justify-between gap-3 ${
                    !item.read ? "bg-primary/5" : ""
                  }`}
                >
                  <div className="space-y-1 flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      {!item.read && <span className="h-2 w-2 rounded-full bg-primary shrink-0" />}
                      <h4 className="text-xs font-bold text-text truncate">{item.title}</h4>
                    </div>
                    <p className="text-xs text-text-secondary leading-relaxed line-clamp-2">
                      {item.message}
                    </p>
                    <span className="text-[10px] text-text-muted font-medium block">
                      {new Date(item.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteNotificationMutation.mutate(item.id);
                    }}
                    title="Delete notification"
                    className="text-text-muted hover:text-error p-1 transition-colors shrink-0"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="p-3 border-t border-border bg-surface-elevated/20 text-center">
              <button
                type="button"
                onClick={() => {
                  setIsOpen(false);
                  navigate("/jobs");
                }}
                className="text-xs font-bold text-primary hover:underline flex items-center justify-center gap-1 w-full"
              >
                View Jobs Pipeline <ExternalLink size={12} />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default NotificationBell;
