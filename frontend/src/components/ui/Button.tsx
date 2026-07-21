/**
 * Button Component
 *
 * The primary interactive element in Finder.
 * Supports multiple visual variants and sizes.
 *
 * Why variants?
 * - "primary" for main actions (Search, Apply, Save)
 * - "secondary" for less important actions (Cancel, Skip)
 * - "ghost" for subtle actions (in toolbars, menus)
 * - "danger" for destructive actions (Delete, Reject)
 */

import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";
import { cn } from "../../lib/utils";

/** Visual style of the button */
type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

/** Size of the button */
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual variant — determines colors and style */
  variant?: ButtonVariant;
  /** Size — affects padding and font size */
  size?: ButtonSize;
  /** Optional icon to display before the label */
  icon?: ReactNode;
  /** Show a loading spinner and disable the button */
  isLoading?: boolean;
  /** Content inside the button */
  children: ReactNode;
}

/**
 * CSS classes for each variant.
 *
 * We use a lookup object instead of a long if/else chain
 * because it's easier to read and extend.
 */
const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-primary text-bg hover:bg-primary-hover shadow-sm active:scale-[0.98]",
  secondary:
    "bg-surface text-text border border-border hover:bg-surface-hover hover:border-border-hover active:scale-[0.98]",
  ghost:
    "bg-transparent text-text-secondary hover:text-text hover:bg-surface-elevated active:scale-[0.98]",
  danger:
    "bg-error/10 text-error hover:bg-error/20 border border-error/20 active:scale-[0.98]",
};

/** CSS classes for each size */
const sizeClasses: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-xs rounded-md gap-1.5",
  md: "h-10 px-4 text-sm rounded-lg gap-2",
  lg: "h-12 px-6 text-base rounded-xl gap-2.5",
};

/**
 * Button — the primary action component.
 *
 * Uses forwardRef so parent components can access the underlying
 * <button> DOM element (needed for focus management, tooltips, etc.)
 */
const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      icon,
      isLoading = false,
      disabled,
      className,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          /* Base styles — shared by all variants */
          "inline-flex items-center justify-center font-medium",
          "transition-all duration-[150ms] ease-out",
          "focus-ring cursor-pointer",
          "disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100",
          /* Variant and size specific styles */
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        {...props}
      >
        {/* Loading spinner replaces the icon when loading */}
        {isLoading ? (
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
        ) : icon ? (
          <span className="shrink-0">{icon}</span>
        ) : null}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";

export default Button;
