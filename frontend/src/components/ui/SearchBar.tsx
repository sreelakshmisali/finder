/**
 * SearchBar Component
 *
 * Input bar for keyword search, location filtering, remote toggle, and provider selecting.
 */

import { useState } from "react";
import { Search, MapPin, SlidersHorizontal, Check } from "lucide-react";
import { Button, Input } from "./index";

interface SearchBarProps {
  onSearch: (params: { query: string; location: string; remoteOnly: boolean; sources: string[] }) => void;
  isLoading?: boolean;
  providers?: { name: string; display_name: string }[];
}

function SearchBar({ onSearch, isLoading, providers = [] }: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("");
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [showFilters, setShowFilters] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch({ query, location, remoteOnly, sources: selectedSources });
  };

  const toggleSource = (sourceName: string) => {
    setSelectedSources((prev) =>
      prev.includes(sourceName)
        ? prev.filter((s) => s !== sourceName)
        : [...prev, sourceName]
    );
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 mb-6">
      <div className="flex flex-col sm:flex-row gap-2">
        {/* Keyword input */}
        <div className="flex-1">
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search title, skills, or company (e.g. Python Engineer)..."
            icon={<Search size={18} />}
          />
        </div>

        {/* Location input */}
        <div className="w-full sm:w-64">
          <Input
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Location or Remote"
            icon={<MapPin size={18} />}
          />
        </div>

        {/* Filter Toggle & Submit */}
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="secondary"
            onClick={() => setShowFilters(!showFilters)}
            className="shrink-0"
            icon={<SlidersHorizontal size={16} />}
          >
            Filters
          </Button>

          <Button
            type="submit"
            variant="primary"
            isLoading={isLoading}
            className="shrink-0"
          >
            Search
          </Button>
        </div>
      </div>

      {/* Expandable Filter Panel */}
      {showFilters && (
        <div className="p-5 glass-card rounded-xl flex flex-col sm:flex-row flex-wrap items-start sm:items-center justify-between gap-4">
          {/* Remote Only Toggle */}
          <label className="flex items-center gap-2 text-sm text-text font-medium cursor-pointer select-none">
            <input
              type="checkbox"
              checked={remoteOnly}
              onChange={(e) => setRemoteOnly(e.target.checked)}
              className="h-4 w-4 rounded border-border bg-surface text-primary focus:ring-primary/40 cursor-pointer"
            />
            Remote positions only
          </label>

          {/* Provider Selection Filter */}
          {providers.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-text-muted font-medium">Sources:</span>
              <div className="flex flex-wrap gap-1.5">
                {providers.map((p) => {
                  const isSelected = selectedSources.length === 0 || selectedSources.includes(p.name);
                  return (
                    <button
                      key={p.name}
                      type="button"
                      onClick={() => toggleSource(p.name)}
                      className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border transition-all cursor-pointer ${
                        isSelected
                          ? "bg-primary-muted text-primary border-primary/40"
                          : "bg-surface-elevated text-text-muted border-border hover:text-text"
                      }`}
                    >
                      {isSelected && <Check size={12} />}
                      {p.display_name}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </form>
  );
}

export default SearchBar;
