/**
 * StatusBadge Component
 *
 * Visual badge displaying application status pills with color coding.
 */

import Badge from "../ui/Badge";
import { STATUS_LABELS, STATUS_COLORS } from "../../lib/constants";

interface StatusBadgeProps {
  status: string;
}

function StatusBadge({ status }: StatusBadgeProps) {
  const label = STATUS_LABELS[status] || status;
  const colorClass = STATUS_COLORS[status] || "text-text-secondary bg-surface-elevated";

  let variant: "default" | "primary" | "success" | "warning" | "error" | "accent" = "default";

  switch (status) {
    case "saved":
      variant = "default";
      break;
    case "approved":
    case "awaiting_confirmation":
      variant = "primary";
      break;
    case "queued":
    case "awaiting_input":
      variant = "warning";
      break;
    case "running":
      variant = "accent";
      break;
    case "completed":
    case "offer":
      variant = "success";
      break;
    case "failed":
    case "rejected":
      variant = "error";
      break;
    case "interview":
      variant = "primary";
      break;
  }

  return (
    <Badge variant={variant} className={`font-semibold px-2.5 py-0.5 text-xs capitalize ${colorClass}`}>
      {label}
    </Badge>
  );
}

export default StatusBadge;
