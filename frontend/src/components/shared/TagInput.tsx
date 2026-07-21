/**
 * TagInput Component
 *
 * An interactive tag selector allowing users to type a value and press Enter/Comma to add a tag pill.
 * Clicking 'X' removes a tag pill.
 */

import { useState, type KeyboardEvent } from "react";
import { X, Plus } from "lucide-react";
import { Badge } from "../ui";

interface TagInputProps {
  tags: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
  label?: string;
  variant?: "primary" | "default" | "accent";
}

function TagInput({
  tags = [],
  onChange,
  placeholder = "Type and press Enter...",
  label,
  variant = "primary",
}: TagInputProps) {
  const [inputValue, setInputValue] = useState("");

  const addTag = () => {
    const trimmed = inputValue.trim();
    if (trimmed && !tags.includes(trimmed)) {
      onChange([...tags, trimmed]);
      setInputValue("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addTag();
    }
  };

  const removeTag = (indexToRemove: number) => {
    onChange(tags.filter((_, idx) => idx !== indexToRemove));
  };

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label className="text-sm font-medium text-text-secondary">
          {label}
        </label>
      )}

      <div className="p-3 bg-surface border border-border rounded-[12px] min-h-[56px] flex flex-wrap items-center gap-2 focus-within:border-primary focus-within:ring-1 focus-within:ring-primary/30 transition-all shadow-sm">
        {tags.map((tag, idx) => (
          <Badge key={idx} variant={variant} className="px-2.5 py-1 text-xs gap-1">
            {tag}
            <button
              type="button"
              onClick={() => removeTag(idx)}
              className="hover:text-text cursor-pointer ml-0.5"
            >
              <X size={12} />
            </button>
          </Badge>
        ))}

        <div className="flex items-center flex-1 min-w-[140px]">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={tags.length === 0 ? placeholder : "Add another..."}
            className="w-full bg-transparent text-sm text-text placeholder:text-text-muted focus:outline-none"
          />
          {inputValue.trim() && (
            <button
              type="button"
              onClick={addTag}
              className="p-1 text-primary hover:text-primary-hover cursor-pointer"
            >
              <Plus size={16} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default TagInput;
