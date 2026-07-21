import Badge from "../ui/Badge";

interface MatchBadgeProps {
  score?: number;
}

function MatchBadge({ score }: MatchBadgeProps) {
  if (score === undefined || score === null) return null;

  let variant: "success" | "warning" | "error" | "primary" = "success";
  if (score < 50) variant = "error";
  else if (score < 80) variant = "warning";
  else if (score >= 90) variant = "primary"; // Add extra pop for great matches

  return (
    <Badge variant={variant} className="font-semibold px-2.5 py-1 text-xs shadow-sm">
      <span className="mr-1.5">⚡</span>
      {Math.round(score)}% Match
    </Badge>
  );
}

export default MatchBadge;
