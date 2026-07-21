import type { ReactNode } from "react";

interface StatCardProps {
  title: string;
  value: string | number;
  icon: ReactNode;
  trend?: string;
  trendPositive?: boolean;
}

function StatCard({ title, value, icon, trend, trendPositive = true }: StatCardProps) {
  return (
    <div className="p-6 rounded-2xl bg-surface border border-border shadow-sm flex flex-col justify-between group hover:shadow-md hover:border-primary/30 transition-all cursor-default min-h-[160px]">
      <div className="flex items-start justify-between mb-4">
        <span className="text-sm font-medium text-text-secondary tracking-wide">
          {title}
        </span>
        <div className="h-12 w-12 rounded-xl bg-surface-elevated border border-border/50 flex items-center justify-center text-text-secondary group-hover:text-primary group-hover:scale-105 group-hover:bg-primary/5 group-hover:border-primary/20 transition-all">
          {icon}
        </div>
      </div>

      <div className="flex items-end justify-between mt-auto">
        <span className="text-3xl font-black tracking-tight text-text group-hover:text-primary transition-colors">
          {value}
        </span>

        {trend && (
          <span
            className={`text-xs font-semibold px-2.5 py-1 rounded-md flex items-center gap-1 shadow-sm ${
              trendPositive
                ? "text-success bg-success/10 border border-success/20"
                : "text-text-muted bg-surface-elevated border border-border/50"
            }`}
          >
            {trend}
          </span>
        )}
      </div>
    </div>
  );
}

export default StatCard;
