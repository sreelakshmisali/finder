/**
 * Utility Functions
 *
 * Small, reusable helper functions used across the app.
 * Each function does one thing well.
 */

/**
 * Conditionally join CSS class names together.
 *
 * Filters out falsy values (undefined, null, false, "", 0)
 * so you can write conditional classes cleanly:
 *
 * @example
 *   cn("base-class", isActive && "active", hasError && "error")
 *
 * @param classes - A list of class names or falsy values
 * @returns A single space-separated string of valid class names
 */
export function cn(...classes: unknown[]): string {
  return classes.filter(Boolean).join(" ");
}

/**
 * Format a number with commas for display.
 *
 * @example formatNumber(1234567) → "1,234,567"
 */
export function formatNumber(num: number): string {
  return num.toLocaleString("en-US");
}

/**
 * Format a salary range for display.
 *
 * @example formatSalary(80000, 120000) → "$80K – $120K"
 * @example formatSalary(80000) → "$80K+"
 * @example formatSalary(undefined, 120000) → "Up to $120K"
 */
export function formatSalary(min?: number, max?: number): string {
  const fmt = (n: number) => `$${Math.round(n / 1000)}K`;

  if (min && max) return `${fmt(min)} – ${fmt(max)}`;
  if (min) return `${fmt(min)}+`;
  if (max) return `Up to ${fmt(max)}`;
  return "Not specified";
}

/**
 * Format a date string into a human-readable relative time.
 *
 * @example formatRelativeDate("2026-07-20T...") → "1 day ago"
 * @example formatRelativeDate("2026-07-21T...") → "Today"
 */
export function formatRelativeDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
  return `${Math.floor(diffDays / 365)} years ago`;
}

/**
 * Format a date string into a short readable format.
 *
 * @example formatDate("2026-07-21T...") → "Jul 21, 2026"
 */
export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/**
 * Truncate text to a maximum length and add ellipsis.
 *
 * @example truncate("Hello World", 5) → "Hello..."
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trimEnd() + "...";
}

/**
 * Get the color class for a match score percentage.
 *
 * - ≥ 80%: Green (strong match)
 * - ≥ 50%: Yellow (decent match)
 * - < 50%: Red (weak match)
 */
export function getMatchColor(score: number): string {
  if (score >= 80) return "text-success";
  if (score >= 50) return "text-warning";
  return "text-error";
}

/**
 * Generate initials from a company or person name.
 *
 * @example getInitials("Google") → "G"
 * @example getInitials("Open AI") → "OA"
 */
export function getInitials(name: string): string {
  return name
    .split(" ")
    .map((word) => word[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

/**
 * Safely strip HTML tags from a string.
 */
export function stripHtml(html: string): string {
  if (!html) return "";
  const doc = new DOMParser().parseFromString(html, "text/html");
  return doc.body.textContent || "";
}
