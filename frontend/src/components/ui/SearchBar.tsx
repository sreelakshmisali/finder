/**
 * SearchBar Component
 *
 * Input bar for keyword search, location filtering, remote toggle, salary threshold,
 * provider selection, auto-generated vs manual override search modes, and Saved Searches.
 * Implements input debouncing (400ms delay) to prevent rapid filter API spam.
 */

import { useState, useEffect, useRef } from "react";
import {
  Search,
  MapPin,
  SlidersHorizontal,
  Check,
  Sparkles,
  DollarSign,
  RefreshCw,
  Bookmark,
  Plus,
  Trash2,
  Play,
} from "lucide-react";
import { Button, Input, Modal } from "./index";
import {
  useSavedSearches,
  useCreateSavedSearch,
  useRunSavedSearch,
  useDeleteSavedSearch,
} from "../../hooks/useSavedSearches";
import type { SavedSearch } from "../../types/savedSearch";
import type { SearchMode } from "../../types/job";

interface SearchBarProps {
  onSearch: (params: {
    query: string;
    location: string;
    remoteOnly: boolean;
    sources: string[];
    searchMode: SearchMode;
    minSalary?: number;
    forceRefresh?: boolean;
  }) => void;
  isLoading?: boolean;
  providers?: { name: string; display_name: string }[];
  suggestedQueries?: string[];
  appliedQuery?: string;
  appliedLocation?: string;
  layout?: "landing" | "header";
}

function SearchBar({
  onSearch,
  isLoading,
  providers = [],
  suggestedQueries = [],
  appliedQuery,
  appliedLocation,
  layout = "header",
}: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("");
  const [minSalary, setMinSalary] = useState<string>("");
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [showFilters, setShowFilters] = useState(false);
  const [searchMode, setSearchMode] = useState<SearchMode>("NORMAL");

  // Saved Searches state & hooks
  const [isSaveModalOpen, setIsSaveModalOpen] = useState(false);
  const [savedSearchName, setSavedSearchName] = useState("");

  const { data: savedSearches = [] } = useSavedSearches();
  const createSavedSearchMutation = useCreateSavedSearch();
  const runSavedSearchMutation = useRunSavedSearch();
  const deleteSavedSearchMutation = useDeleteSavedSearch();

  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Sync displayed query with applied query
  useEffect(() => {
    if (appliedQuery && !query) {
      setQuery(appliedQuery);
    }
  }, [appliedQuery]);

  // Execute debounced search when user modifies filters ONLY if they are already in the header layout
  // (i.e. they have already initiated a search). We don't auto-search from the landing page.
  useEffect(() => {
    if (layout === "landing") {
      return;
    }

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(() => {
      executeSearch(false);
    }, 400); // 400ms debounce delay

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [query, location, minSalary, remoteOnly, selectedSources, searchMode]);

  const executeSearch = (forceRefresh = false) => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    onSearch({
      query: query.trim(),
      location: location.trim(),
      remoteOnly,
      sources: selectedSources,
      searchMode,
      minSalary: minSalary ? Number(minSalary) : undefined,
      forceRefresh,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    executeSearch(false);
  };

    const handleChipClick = (suggested: string) => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    setQuery(suggested);
    setSearchMode("NORMAL");
    onSearch({
      query: suggested,
      location: location.trim(),
      remoteOnly,
      sources: selectedSources,
      searchMode: "NORMAL",
      minSalary: minSalary ? Number(minSalary) : undefined,
      forceRefresh: false,
    });
  };

  const toggleSource = (sourceName: string) => {
    setSelectedSources((prev) =>
      prev.includes(sourceName)
        ? prev.filter((s) => s !== sourceName)
        : [...prev, sourceName]
    );
  };

  // Saved Search Handlers
  const handleOpenSaveModal = () => {
    const defaultName = query.trim()
      ? `${query.trim()} ${location.trim() ? location.trim() : "Jobs"}`
      : "Saved Job Search";
    setSavedSearchName(defaultName);
    setIsSaveModalOpen(true);
  };

  const handleConfirmSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (!savedSearchName.trim()) return;

    const filterObj = {
      location: location.trim(),
      remote_only: remoteOnly,
      sources: selectedSources,
      min_salary: minSalary ? Number(minSalary) : undefined,
    };

    createSavedSearchMutation.mutate(
      {
        name: savedSearchName.trim(),
        query: query.trim() || undefined,
        filters: filterObj,
        mode: searchMode,
      },
      {
        onSuccess: () => {
          setIsSaveModalOpen(false);
          setSavedSearchName("");
        },
      }
    );
  };

  const handleRunSavedSearch = (saved: SavedSearch) => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    const savedFilters = saved.filters || {};
    const sq = saved.query || "";
    const sloc = savedFilters.location || "";
    const srem = Boolean(savedFilters.remote_only);
    const ssources = savedFilters.sources || [];
    const sminSal = savedFilters.min_salary ? String(savedFilters.min_salary) : "";
    const smode = saved.mode || "NORMAL";

    setQuery(sq);
    setLocation(sloc);
    setRemoteOnly(srem);
    setSelectedSources(ssources);
    setMinSalary(sminSal);
    setSearchMode(smode);

    runSavedSearchMutation.mutate(saved.id);

    onSearch({
      query: sq,
      location: sloc,
      remoteOnly: srem,
      sources: ssources,
      searchMode: smode,
      minSalary: savedFilters.min_salary,
      forceRefresh: true,
    });
  };

  const handleDeleteSavedSearch = (e: React.MouseEvent, searchId: string) => {
    e.stopPropagation();
    deleteSavedSearchMutation.mutate(searchId);
  };

  return (
    <>
      <form onSubmit={handleSubmit} className={`flex flex-col gap-3.5 ${layout === "landing" ? "w-full max-w-3xl mx-auto" : "mb-6"}`}>
        {/* Top Controls */}
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex items-center flex-wrap gap-2">
            <label className="flex items-center gap-2 text-sm text-text font-bold cursor-pointer select-none bg-surface-elevated px-3 py-1.5 rounded-full border border-border hover:border-primary/40 transition-colors">
              <input
                type="checkbox"
                checked={searchMode === "SMART"}
                onChange={(e) => setSearchMode(e.target.checked ? "SMART" : "NORMAL")}
                className="h-4 w-4 rounded border-border bg-surface text-primary focus:ring-primary/40 cursor-pointer"
              />
              ✨ Search using my Resume
            </label>
            {layout === "header" && appliedQuery && (
              <span className="text-text-muted hidden sm:inline">
                Active query: <strong className="text-text font-semibold">"{appliedQuery}"</strong>
                {appliedLocation ? <span className="ml-1 font-normal">in <strong>"{appliedLocation}"</strong></span> : null}
              </span>
            )}
          </div>

          <div className="flex items-center gap-3">
            {/* Save Current Search CTA */}
            <button
              type="button"
              onClick={handleOpenSaveModal}
              title="Save current search query and filters for quick reuse"
              className="text-xs text-primary font-bold hover:underline flex items-center gap-1 cursor-pointer transition-colors"
            >
              <Bookmark size={13} /> Save This Search
            </button>

            {/* Force Refresh CTA */}
            <button
              type="button"
              onClick={() => executeSearch(true)}
              title="Bypass search cache and fetch live jobs from providers"
              className="text-xs text-text-muted hover:text-text font-semibold flex items-center gap-1 cursor-pointer transition-colors"
            >
              <RefreshCw size={12} className={isLoading ? "animate-spin text-primary" : ""} /> Force Refresh
            </button>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-2">
          {/* Keyword input */}
          <div className="flex-1">
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search title, skills, or company (e.g. Python Engineer)..."
              icon={<Search size={18} />}
              disabled={searchMode === "SMART"}
              className={searchMode === "SMART" ? "opacity-50 cursor-not-allowed" : ""}
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
              Apply Filters
            </Button>
          </div>
        </div>

        {/* Saved Searches Row */}
        {savedSearches.length > 0 && layout === "header" && (
          <div className="flex items-center flex-wrap gap-2 pt-1 text-xs">
            <span className="text-text-muted font-bold flex items-center gap-1">
              <Bookmark size={13} className="text-primary" /> Saved Searches:
            </span>
            <div className="flex flex-wrap gap-1.5">
              {savedSearches.map((s) => (
                <div
                  key={s.id}
                  onClick={() => handleRunSavedSearch(s)}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-primary/30 bg-primary/5 text-primary hover:bg-primary/10 hover:border-primary font-semibold transition-all cursor-pointer shadow-sm group"
                >
                  <Play size={11} className="fill-current text-primary" />
                  <span>{s.name}</span>
                  <button
                    type="button"
                    onClick={(e) => handleDeleteSavedSearch(e, s.id)}
                    title="Delete saved search"
                    className="hover:text-error text-text-muted transition-colors ml-1 p-0.5"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Suggested Search Query Chips */}
        {suggestedQueries.length > 0 && layout === "header" && (
          <div className="flex items-center flex-wrap gap-2 pt-1 text-xs">
            <span className="text-text-muted font-bold flex items-center gap-1">
              <Sparkles size={13} className="text-accent" /> Resume Suggestions:
            </span>
            <div className="flex flex-wrap gap-1.5">
              {suggestedQueries.map((sq) => {
                const isCurrent = query.toLowerCase().trim() === sq.toLowerCase().trim();
                return (
                  <button
                    key={sq}
                    type="button"
                    onClick={() => handleChipClick(sq)}
                    className={`px-2.5 py-1 rounded-full border font-semibold transition-all cursor-pointer ${
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

      {/* Save Search Rule Modal */}
      <Modal
        isOpen={isSaveModalOpen}
        onClose={() => setIsSaveModalOpen(false)}
        title="Save Search Rule"
        size="md"
      >
        <form onSubmit={handleConfirmSave} className="space-y-5">
          <div className="space-y-1">
            <label className="block text-xs font-bold text-text">Search Rule Name</label>
            <Input
              value={savedSearchName}
              onChange={(e) => setSavedSearchName(e.target.value)}
              placeholder="e.g. Python Remote Jobs"
              required
              autoFocus
            />
          </div>

          <div className="p-4 rounded-xl bg-surface-elevated border border-border text-xs space-y-2">
            <div className="font-bold text-text mb-1 flex items-center gap-1.5">
              <Bookmark size={14} className="text-primary" /> Active Rule Payload Summary:
            </div>
            <div><strong className="text-text">Mode:</strong> {searchMode}</div>
            <div><strong className="text-text">Query:</strong> {query.trim() || "(None)"}</div>
            <div><strong className="text-text">Location:</strong> {location.trim() || "(Any)"}</div>
            <div><strong className="text-text">Remote Only:</strong> {remoteOnly ? "Yes" : "No"}</div>
            {minSalary && <div><strong className="text-text">Min Salary:</strong> ${Number(minSalary).toLocaleString()}/yr</div>}
          </div>

          <div className="flex items-center justify-end gap-3 pt-2 border-t border-border">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => setIsSaveModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={createSavedSearchMutation.isPending}
              icon={<Plus size={14} />}
            >
              Save Search Rule
            </Button>
          </div>
        </form>
      </Modal>
    </>
  );
}

export default SearchBar;
