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
 * Navigation items for the sidebar.
 * Each item maps to a route and an icon name from lucide-react.
 */
export const NAV_ITEMS = [
  { label: "Job Search", path: "/jobs", icon: "Search" },
  { label: "Profile", path: "/profile", icon: "UserCheck" },
] as const;
