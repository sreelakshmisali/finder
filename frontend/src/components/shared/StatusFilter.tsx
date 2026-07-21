/**
 * StatusFilter Component
 *
 * Horizontal tab navigation bar for filtering applications by status.
 */

interface StatusFilterProps {
  selectedStatus: string;
  onSelectStatus: (status: string) => void;
  counts?: Record<string, number>;
}

const FILTER_OPTIONS = [
  { id: "all", label: "All" },
  { id: "saved", label: "Saved" },
  { id: "approved", label: "Approved" },
  { id: "completed", label: "Applied" },
  { id: "interview", label: "Interview" },
  { id: "offer", label: "Offers" },
  { id: "rejected", label: "Rejected" },
];

function StatusFilter({ selectedStatus = "all", onSelectStatus, counts }: StatusFilterProps) {
  return (
    <div className="flex flex-nowrap overflow-x-auto items-center gap-2 p-2 glass rounded-[16px] border border-border">
      {FILTER_OPTIONS.map((opt) => {
        const isSelected = selectedStatus === opt.id;
        const count = counts?.[opt.id];

        return (
          <button
            key={opt.id}
            type="button"
            onClick={() => onSelectStatus(opt.id)}
            className={`px-4 py-2 rounded-[12px] text-sm font-semibold transition-all cursor-pointer flex items-center gap-2 ${
              isSelected
                ? "bg-primary text-white shadow-md"
                : "text-text-secondary hover:text-text hover:bg-surface-elevated"
            }`}
          >
            <span>{opt.label}</span>
            {count !== undefined && (
              <span
                className={`px-1.5 py-0.2 text-[10px] rounded-full ${
                  isSelected ? "bg-white/20 text-white" : "bg-surface-elevated text-text-muted"
                }`}
              >
                {count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

export default StatusFilter;
