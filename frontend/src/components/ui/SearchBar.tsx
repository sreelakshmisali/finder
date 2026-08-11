/**
 * SearchBar Component
 *
 * Implements two distinct search methods:
 * 1. Standard Search: Uses keyword & location inputs. (Keyword required).
 * 2. Search with Resume: Uses active resume context + optional keyword & location.
 *
 * Also displays active resume status and suggested search chips with auto-search execution.
 */

import React, { useState, useEffect, useRef } from "react";
import { Search, MapPin, Sparkles, FileText, AlertCircle } from "lucide-react";
import { Button, Input } from "./index";
interface SearchBarProps {
  onSearch: (params: {
    query: string;
    location: string;
    remoteOnly?: boolean;
    forceRefresh?: boolean;
  }) => void;
  isLoading?: boolean;
  activeResumeFilename?: string | null;
  suggestedQueries?: string[];
  appliedQuery?: string;
  appliedLocation?: string;
}

function SearchBar({
  onSearch,
  isLoading,
  activeResumeFilename,
  suggestedQueries = [],
  appliedQuery,
  appliedLocation,
}: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  const keywordInputRef = useRef<HTMLInputElement>(null);

  // Sync displayed query with applied query on initial load
  useEffect(() => {
    if (appliedQuery && !query) {
      setQuery(appliedQuery);
    }
  }, [appliedQuery]);

  // Clear validation error when user types in keyword input
  const handleQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    if (validationError) {
      setValidationError(null);
    }
  };

  /**
   * Standard Search: Keyword is required.
   */
  const handleStandardSearch = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) {
      setValidationError("Please enter a job title or keyword for standard search.");
      keywordInputRef.current?.focus();
      return;
    }
    setValidationError(null);
    onSearch({
      query: trimmed,
      location: location.trim(),
    });
  };

  /**
   * Search with Resume: Keyword is optional.
   */
  const handleSearchWithResume = () => {
    setValidationError(null);
    onSearch({
      query: query.trim(),
      location: location.trim(),
    });
  };

  /**
   * Suggested Chip Click Workflow:
   * 1. Populate keyword
   * 2. Focus keyword input
   * 3. Execute Search with Resume automatically
   * 4. Preserve keyword in input
   */
  const handleChipClick = (suggested: string) => {
    setQuery(suggested);
    setValidationError(null);
    if (keywordInputRef.current) {
      keywordInputRef.current.focus();
    }
    onSearch({
      query: suggested,
      location: location.trim(),
    });
  };

  const hasActiveResume = Boolean(activeResumeFilename);

  return (
    <div className="flex flex-col gap-4">
      {/* Active Search Summary Line */}
      {appliedQuery && (
        <div className="text-xs text-text-muted">
          Active search: <strong className="text-text font-semibold">"{appliedQuery}"</strong>
          {appliedLocation ? <span className="ml-1 font-normal">in <strong>"{appliedLocation}"</strong></span> : null}
        </div>
      )}

      {/* Input Row: Keyword & Location */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Keyword input */}
        <div className="flex-1 space-y-1">
          <Input
            ref={keywordInputRef}
            value={query}
            onChange={handleQueryChange}
            placeholder="Job title, skill, or keyword (e.g. Python Developer)..."
            icon={<Search size={18} />}
          />
          {validationError && (
            <div className="flex items-center gap-1.5 text-xs text-error font-medium pt-0.5 animate-in fade-in">
              <AlertCircle size={13} />
              <span>{validationError}</span>
            </div>
          )}
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
      </div>

      {/* Buttons Row & Active Resume Indicator */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
        {/* Active Resume Context Indicator */}
        <div className="flex items-center gap-2 text-xs">
          {hasActiveResume ? (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-elevated/70 border border-border text-text-secondary">
              <FileText size={14} className="text-primary" />
              <span>Active Resume: <strong className="text-text font-semibold">{activeResumeFilename}</strong></span>
            </div>
          ) : (
            <span className="text-text-muted text-xs">Upload a resume to enable Search with Resume</span>
          )}
        </div>

        {/* Search Action Buttons */}
        <div className="flex items-center gap-2.5">
          {/* Standard Search Button */}
          <Button
            type="button"
            variant="secondary"
            isLoading={isLoading}
            onClick={() => handleStandardSearch()}
            className="font-semibold px-5 text-sm"
            icon={<Search size={15} />}
          >
            Search
          </Button>

          {/* Search with Resume Button */}
          <Button
            type="button"
            variant="primary"
            disabled={!hasActiveResume}
            isLoading={isLoading}
            onClick={handleSearchWithResume}
            className="font-bold px-6 text-sm shadow-md"
            icon={<Sparkles size={16} />}
            title={!hasActiveResume ? "Upload a resume to enable Search with Resume" : "Search using active resume context"}
          >
            Search with Resume
          </Button>
        </div>
      </div>

      {/* Suggested Search Query Chips */}
      {hasActiveResume && suggestedQueries.length > 0 && (
        <div className="flex flex-col gap-2 pt-2 border-t border-border/50 text-xs">
          <div className="flex items-center justify-between">
            <span className="text-text font-bold flex items-center gap-1.5">
              <Sparkles size={14} className="text-accent" /> Suggested from your Active Resume:
            </span>
            <span className="text-[11px] text-text-muted italic hidden sm:inline">
              Click a suggestion to search immediately
            </span>
          </div>

          <div className="flex flex-wrap gap-2">
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
    </div>
  );
}

export default SearchBar;
