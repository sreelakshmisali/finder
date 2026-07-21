/**
 * Application Constants
 *
 * Central place for all magic strings and values used across the app.
 * Instead of scattering "Saved", "Approved", etc. throughout components,
 * we define them here once and import where needed.
 */

/** The display name of the application */
export const APP_NAME = "Finder";

/**
 * All possible statuses for a job application.
 * These match the backend's status enum exactly.
 */
export const APPLICATION_STATUSES = {
  SAVED: "saved",
  APPROVED: "approved",
  QUEUED: "queued",
  RUNNING: "running",
  AWAITING_INPUT: "awaiting_input",
  AWAITING_CONFIRMATION: "awaiting_confirmation",
  COMPLETED: "completed",
  FAILED: "failed",
  INTERVIEW: "interview",
  REJECTED: "rejected",
  OFFER: "offer",
} as const;

/**
 * Human-readable labels for each application status.
 * Used in the UI to display friendly text instead of raw status codes.
 */
export const STATUS_LABELS: Record<string, string> = {
  saved: "Saved",
  approved: "Approved",
  queued: "Queued",
  running: "Running",
  awaiting_input: "Awaiting Input",
  awaiting_confirmation: "Review & Submit",
  completed: "Applied",
  failed: "Failed",
  interview: "Interview",
  rejected: "Rejected",
  offer: "Offer",
};

/**
 * Color mappings for each status — used by StatusBadge component.
 * These are TailwindCSS color class segments.
 */
export const STATUS_COLORS: Record<string, string> = {
  saved: "text-text-secondary bg-surface-elevated",
  approved: "text-primary bg-primary-muted",
  queued: "text-warning bg-warning-muted",
  running: "text-accent bg-accent/15",
  awaiting_input: "text-warning bg-warning-muted",
  awaiting_confirmation: "text-primary bg-primary-muted",
  completed: "text-success bg-success-muted",
  failed: "text-error bg-error-muted",
  interview: "text-primary bg-primary-muted",
  rejected: "text-error bg-error-muted",
  offer: "text-success bg-success-muted",
};

/**
 * Navigation items for the sidebar.
 * Each item maps to a route and an icon name from lucide-react.
 */
export const NAV_ITEMS = [
  { label: "Dashboard", path: "/", icon: "LayoutDashboard" },
  { label: "Jobs", path: "/jobs", icon: "Search" },
  { label: "Resume", path: "/resume", icon: "FileText" },
  { label: "Preferences", path: "/preferences", icon: "SlidersHorizontal" },
  { label: "Tracker", path: "/tracker", icon: "ClipboardList" },
] as const;
