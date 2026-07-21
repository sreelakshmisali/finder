/**
 * Badge Component
 *
 * A small label used to display short metadata like
 * "Remote", "Full-time", "Python", "92% Match".
 *
 * Variants map to the status/category colors from our design system.
 */

import { type HTMLAttributes, type ReactNode } from "react";
import { cn } from "../../lib/utils";

type BadgeVariant =
  | "default"
  | "primary"
  | "success"
  | "warning"
  | "error"
  | "accent";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  /** Visual style of the badge */
  variant?: BadgeVariant;
  /** Content inside — usually short text like "Remote" or "95%" */
  children: ReactNode;
}

/** Color classes for each variant */
const variantClasses: Record<BadgeVariant, string> = {
  default: "bg-surface text-text-secondary border border-border",
  primary: "bg-primary-muted text-primary border border-primary/20",
  success: "bg-success-muted text-success border border-success/20",
  warning: "bg-warning-muted text-warning border border-warning/20",
  error: "bg-error-muted text-error border border-error/20",
  accent: "bg-accent/10 text-accent border border-accent/20",
};

/**
 * Badge — a compact label for metadata.
 *
 * @example
 *   <Badge variant="success">Remote</Badge>
 *   <Badge variant="primary">Python</Badge>
 */
function Badge({
  variant = "default",
  children,
  className,
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5",
        "text-xs font-medium rounded-full",
        "transition-colors duration-[150ms]",
        variantClasses[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}

export default Badge;
