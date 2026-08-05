/**
 * SearchBar Component
 *
 * Input bar for keyword search, location filtering, remote toggle, salary threshold,
 * and resume suggestion chips. Implements input debouncing (400ms delay).
 */

import { useState, useEffect, useRef } from "react";
import {
  Search,
  MapPin,
  SlidersHorizontal,
  Sparkles,
  DollarSign,
  RefreshCw,
} from "lucide-react";
import { Button, Input } from "./index";
import type { SearchMode } from "../../types/job";

interface SearchBarProps {
  onSearch: (params: {
    query: string;
    location: string;
    remoteOnly: boolean;
    searchMode?: SearchMode;
    minSalary?: number;
    forceRefresh?: boolean;
  }) => void;
  isLoading?: boolean;
  suggestedQueries?: string[];
  appliedQuery?: string;
  appliedLocation?: string;
  layout?: "landing" | "header";
}

function SearchBar({
  onSearch,
  isLoading,
  suggestedQueries = [],
  appliedQuery,
  appliedLocation,
  layout = "header",
}: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("");
  const [minSalary, setMinSalary] = useState<string>("");
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Sync displayed query with applied query
  useEffect(() => {
    if (appliedQuery && !query) {
      setQuery(appliedQuery);
    }
  }, [appliedQuery]);

  // Execute debounced search when user modifies filters in header layout
  useEffect(() => {
    if (layout === "landing") {
      return;
    }

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(() => {
      executeSearch(false);
    }, 400);

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [query, location, minSalary, remoteOnly]);

  const executeSearch = (forceRefresh = false, overrideQuery?: string) => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    const targetQuery = (overrideQuery !== undefined ? overrideQuery : query).trim();
    onSearch({
      query: targetQuery,
      location: location.trim(),
      remoteOnly,
      searchMode: "NORMAL",
      minSalary: minSalary ? Number(minSalary) : undefined,
      forceRefresh,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    executeSearch(false);
  };

  const handleChipClick = (suggested: string) => {
    setQuery(suggested);
    executeSearch(false, suggested);
  };

  return (
    <form onSubmit={handleSubmit} className={`flex flex-col gap-3.5 ${layout === "landing" ? "w-full max-w-3xl mx-auto" : "mb-6"}`}>
      {/* Top Bar Status & Live Refresh */}
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center flex-wrap gap-2">
          {appliedQuery && (
            <span className="text-text-muted text-xs">
              Active search: <strong className="text-text font-semibold">"{appliedQuery}"</strong>
              {appliedLocation ? <span className="ml-1 font-normal">in <strong>"{appliedLocation}"</strong></span> : null}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => executeSearch(true)}
            title="Fetch fresh live results"
            className="text-xs text-text-muted hover:text-text font-semibold flex items-center gap-1 cursor-pointer transition-colors"
          >
            <RefreshCw size={12} className={isLoading ? "animate-spin text-primary" : ""} /> Refresh Results
          </button>
        </div>
      </div>

      {/* Main Search Bar Inputs */}
      <div className="flex flex-col sm:flex-row gap-2">
        {/* Keyword input */}
        <div className="flex-1">
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Job title, skill, or keyword (e.g. Python Developer)..."
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

        {/* Filter Toggle & Search CTA */}
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
            className="shrink-0 font-bold px-6"
            icon={<Search size={16} />}
          >
            Search
          </Button>
        </div>
      </div>

      {/* Suggested Search Query Chips (Resume-driven shortcuts) */}
      {suggestedQueries.length > 0 && (
        <div className="flex items-center flex-wrap gap-2 pt-1 text-xs">
          <span className="text-text-muted font-bold flex items-center gap-1.5 shrink-0">
            <Sparkles size={14} className="text-accent" /> Suggested from your resume:
          </span>
          <div className="flex flex-wrap gap-1.5">
            {suggestedQueries.map((sq) => {
              const isCurrent = query.toLowerCase().trim() === sq.toLowerCase().trim();
              return (
                <button
                  key={sq}
                  type="button"
                  onClick={() => handleChipClick(sq)}
                  className={`px-3 py-1 rounded-full border font-semibold text-xs transition-all cursor-pointer ${
                    isCurrent
                      ? "bg-primary text-white border-primary shadow-sm"
                      : "bg-surface-elevated/80 border-border text-text-secondary hover:text-text hover:border-primary/40 hover:bg-surface-elevated"
                  }`}
                >
                  {sq}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Expandable Filter Panel */}
      {showFilters && (
        <div className="p-5 glass-card rounded-xl flex flex-col sm:flex-row flex-wrap items-start sm:items-center justify-between gap-6 animate-in fade-in duration-200 mt-2">
          {/* Min Salary Input */}
          <div className="w-full sm:w-48">
            <label className="block text-xs font-bold text-text mb-1">
              Min Salary ($/yr)
            </label>
            <Input
              type="number"
              value={minSalary}
              onChange={(e) => setMinSalary(e.target.value)}
              placeholder="e.g. 100000"
              icon={<DollarSign size={16} />}
            />
          </div>

          {/* Remote Only Toggle */}
          <div className="pt-5 sm:pt-0">
            <label className="flex items-center gap-2 text-sm text-text font-medium cursor-pointer select-none">
              <input
                type="checkbox"
                checked={remoteOnly}
                onChange={(e) => setRemoteOnly(e.target.checked)}
                className="h-4 w-4 rounded border-border bg-surface text-primary focus:ring-primary/40 cursor-pointer"
              />
              Remote positions only
            </label>
          </div>
        </div>
      )}
    </form>
  );
}

export default SearchBar;
