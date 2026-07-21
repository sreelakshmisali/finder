/**
 * Card Component
 *
 * A container with the glassmorphism effect from our design system.
 * Used everywhere: job cards, stat cards, detail panels, forms.
 *
 * The glass effect creates a subtle frosted look with:
 * - Semi-transparent background
 * - Backdrop blur
 * - Thin border
 */

import { type HTMLAttributes, type ReactNode } from "react";
import { cn } from "../../lib/utils";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Content inside the card */
  children: ReactNode;
  /** Add a hover effect (brightens on hover) */
  hoverable?: boolean;
  /** Remove padding — useful when the card contains a table or list */
  noPadding?: boolean;
}

/**
 * Card — a glassmorphism container.
 *
 * @example
 *   <Card hoverable>
 *     <h3>Job Title</h3>
 *     <p>Company Name</p>
 *   </Card>
 */
function Card({
  children,
  hoverable = false,
  noPadding = false,
  className,
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        /* Glass effect — the signature Finder look */
        "glass-card rounded-xl md:rounded-2xl",
        /* Padding — can be disabled for tables/lists */
        !noPadding && "p-5 md:p-6",
        /* Hover effect — optional brightness change */
        hoverable && "cursor-pointer hover:-translate-y-0.5",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

/**
 * CardHeader — a header section inside a Card.
 * Typically contains a title and optional actions.
 */
function CardHeader({
  children,
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex items-center justify-between mb-4", className)}
      {...props}
    >
      {children}
    </div>
  );
}

/**
 * CardTitle — the title text inside a CardHeader.
 */
function CardTitle({
  children,
  className,
  ...props
}: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn("text-base font-semibold text-text", className)}
      {...props}
    >
      {children}
    </h3>
  );
}

export { Card, CardHeader, CardTitle };
export default Card;
