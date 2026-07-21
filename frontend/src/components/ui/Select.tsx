/**
 * Select Component
 *
 * A styled dropdown select input with label and error support.
 * Consistent with Input component styling.
 */

import { forwardRef, type SelectHTMLAttributes } from "react";
import { cn } from "../../lib/utils";
import { ChevronDown } from "lucide-react";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  /** Label text displayed above the select */
  label?: string;
  /** Error message displayed below */
  error?: string;
  /** Options to display in the dropdown */
  options: { value: string; label: string }[];
  /** Placeholder text shown when no value is selected */
  placeholder?: string;
}

/**
 * Select — a styled dropdown.
 *
 * @example
 *   <Select
 *     label="Work Type"
 *     options={[
 *       { value: "remote", label: "Remote" },
 *       { value: "hybrid", label: "Hybrid" },
 *       { value: "onsite", label: "On-site" },
 *     ]}
 *   />
 */
const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, options, placeholder, className, id, ...props }, ref) => {
    const selectId =
      id || `select-${label?.toLowerCase().replace(/\s+/g, "-")}`;

    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={selectId}
            className="text-sm font-medium text-text-secondary"
          >
            {label}
          </label>
        )}

        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            className={cn(
              "w-full bg-surface border border-border rounded-lg",
              "h-10 px-3 text-sm text-text",
              "focus:outline-none focus:border-border-hover focus:ring-1 focus:ring-border-hover",
              "transition-all duration-200",
              "appearance-none cursor-pointer",
              error && "border-error/50 focus:border-error focus:ring-error/20",
              className
            )}
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>

          {/* Custom dropdown arrow icon */}
          <ChevronDown
            size={16}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none"
          />
        </div>

        {error && <p className="text-xs text-error">{error}</p>}
      </div>
    );
  }
);

Select.displayName = "Select";

export default Select;
