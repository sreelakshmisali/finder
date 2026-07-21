/**
 * Input Component
 *
 * A styled text input field with label and error message support.
 *
 * Why a custom Input component?
 * - Consistent styling across all forms
 * - Built-in label and error display
 * - Accessible by default (label linked to input via htmlFor)
 */

import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  /** Label text displayed above the input */
  label?: string;
  /** Error message displayed below the input (turns border red) */
  error?: string;
  /** Optional icon to show inside the input on the left */
  icon?: React.ReactNode;
}

/**
 * Input — styled text input with optional label and error.
 *
 * Uses forwardRef for compatibility with form libraries
 * like react-hook-form that need direct DOM access.
 */
const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, icon, className, id, ...props }, ref) => {
    /*
     * Generate a unique ID if none provided.
     * This links the <label> to the <input> for accessibility —
     * clicking the label focuses the input.
     */
    const inputId = id || `input-${label?.toLowerCase().replace(/\s+/g, "-")}`;

    return (
      <div className="flex flex-col gap-1.5">
        {/* Label */}
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-medium text-text-secondary"
          >
            {label}
          </label>
        )}

        {/* Input wrapper — needed for the optional icon */}
        <div className="relative">
          {/* Left icon (optional) */}
          {icon && (
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">
              {icon}
            </span>
          )}

          <input
            ref={ref}
            id={inputId}
            className={cn(
              /* Base styles */
              "w-full bg-surface border border-border rounded-lg",
              "h-10 px-3 text-sm text-text",
              "placeholder:text-text-muted",
              /* Focus state */
              "focus:outline-none focus:border-border-hover focus:ring-1 focus:ring-border-hover",
              /* Transition */
              "transition-all duration-200",
              /* Error state — red border */
              error && "border-error/50 focus:border-error focus:ring-error/20",
              /* Adjust padding when icon is present */
              icon && "pl-9",
              className
            )}
            {...props}
          />
        </div>

        {/* Error message */}
        {error && <p className="text-xs text-error">{error}</p>}
      </div>
    );
  }
);

Input.displayName = "Input";

export default Input;
