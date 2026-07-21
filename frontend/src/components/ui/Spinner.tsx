/**
 * Spinner Component
 *
 * A simple animated loading indicator.
 * Used while data is being fetched from the API.
 */

import { cn } from "../../lib/utils";

interface SpinnerProps {
  /** Size of the spinner */
  size?: "sm" | "md" | "lg";
  /** Additional CSS classes */
  className?: string;
}

/** Pixel sizes for each named size */
const sizeClasses: Record<string, string> = {
  sm: "h-4 w-4 border-2",
  md: "h-8 w-8 border-2",
  lg: "h-12 w-12 border-3",
};

/**
 * Spinner — an animated loading circle.
 *
 * Uses CSS border trick:
 * - A full circle with a colored border
 * - One side is transparent (border-t-transparent)
 * - CSS `animate-spin` rotates it continuously
 *
 * @example <Spinner size="lg" />
 */
function Spinner({ size = "md", className }: SpinnerProps) {
  return (
    <div
      className={cn(
        "animate-spin rounded-full border-primary border-t-transparent",
        sizeClasses[size],
        className
      )}
      role="status"
      aria-label="Loading"
    >
      {/* Screen reader accessible text */}
      <span className="sr-only">Loading...</span>
    </div>
  );
}

export default Spinner;
