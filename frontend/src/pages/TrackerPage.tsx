/**
 * Tracker Page Component
 *
 * Full Job Application Tracker dashboard:
 * - Filter applications by status (All, Saved, Approved, Applied, Interview, Offer, Rejected)
 * - Application table with live status transition menus
 * - Playwright Automation modal runner with explicit user confirmation safety
 * - Slide-over modal with application details, notes editor, and status audit trail logs
 */

import { useState } from "react";
import Header from "../components/layout/Header";
import PageWrapper from "../components/layout/PageWrapper";
import StatusFilter from "../components/shared/StatusFilter";
import ApplicationTable from "../components/shared/ApplicationTable";
import ApplicationDetail from "../components/shared/ApplicationDetail";
import AutomationModal from "../components/shared/AutomationModal";
import EmptyState from "../components/shared/EmptyState";
import { Modal, Spinner, Input } from "../components/ui";
import {
  useApplications,
  useUpdateApplicationStatus,
  useUpdateApplicationNotes,
  useStartAutomation,
  useConfirmSubmit,
} from "../hooks/useApplications";
import type { Application } from "../types/application";
import type { AutomationStateResponse } from "../types/automation";
import { ClipboardList, Search } from "lucide-react";

function TrackerPage() {
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedApp, setSelectedApp] = useState<Application | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  // Automation Modal state
  const [automationApp, setAutomationApp] = useState<Application | null>(null);
  const [automationState, setAutomationState] = useState<AutomationStateResponse | null>(null);
  const [isAutoModalOpen, setIsAutoModalOpen] = useState(false);

  const { data: appsData, isLoading, isError } = useApplications(
    selectedStatus === "all" ? undefined : selectedStatus
  );

  const updateStatusMutation = useUpdateApplicationStatus();
  const updateNotesMutation = useUpdateApplicationNotes();
  const startAutoMutation = useStartAutomation();
  const confirmSubmitMutation = useConfirmSubmit();

  const handleUpdateStatus = (id: string, newStatus: string) => {
    updateStatusMutation.mutate({ id, status: newStatus });
  };

  const handleSaveNotes = (id: string, notes: string) => {
    updateNotesMutation.mutate({ id, notes });
  };

  const handleSelectApp = (app: Application) => {
    setSelectedApp(app);
    setIsDetailModalOpen(true);
  };

  const handleStartApply = (app: Application) => {
    setAutomationApp(app);
    setAutomationState(null);
    setIsAutoModalOpen(true);
  };

  const handleRunAutomation = () => {
    if (!automationApp) return;
    startAutoMutation.mutate(
      { applicationId: automationApp.id },
      {
        onSuccess: (state) => {
          setAutomationState(state);
        },
      }
    );
  };

  const handleConfirmSubmit = (answers: Record<string, string>) => {
    if (!automationApp) return;
    confirmSubmitMutation.mutate(
      { applicationId: automationApp.id, answers },
      {
        onSuccess: () => {
          setIsAutoModalOpen(false);
          setAutomationApp(null);
        },
      }
    );
  };

  const applications = appsData?.applications || [];

  // Filter applications by search query if text is entered
  const filteredApps = applications.filter((app) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      app.job.title.toLowerCase().includes(q) ||
      app.job.company.toLowerCase().includes(q) ||
      app.job.location.toLowerCase().includes(q)
    );
  });

  // Compute status counts for filter tab badges
  const counts: Record<string, number> = {
    all: applications.length,
    saved: applications.filter((a) => a.status === "saved").length,
    approved: applications.filter((a) => a.status === "approved").length,
    completed: applications.filter((a) => a.status === "completed").length,
    interview: applications.filter((a) => a.status === "interview").length,
    offer: applications.filter((a) => a.status === "offer").length,
    rejected: applications.filter((a) => a.status === "rejected").length,
  };

  return (
    <>
      <Header
        title="Application Tracker"
        subtitle="Manage and track application statuses from Saved to Interview and Offer"
      />

      <PageWrapper>
        <div className="max-w-7xl mx-auto w-full space-y-6">
          {/* Status Filter Tabs & Search Bar */}
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 w-full">
            <StatusFilter
            selectedStatus={selectedStatus}
            onSelectStatus={setSelectedStatus}
            counts={counts}
          />

          <div className="w-full md:w-64">
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search applications..."
              icon={<Search size={16} />}
            />
          </div>
        </div>

        {/* Loading Spinner */}
        {isLoading && (
          <div className="flex justify-center py-24">
            <Spinner size="lg" />
          </div>
        )}

        {/* Error Notice */}
        {isError && (
          <div className="mb-6 p-4 glass border border-error/30 rounded-[12px] text-error text-sm">
            Failed to load applications. Check backend connection.
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !isError && filteredApps.length === 0 && (
          <EmptyState
            icon={<ClipboardList size={48} />}
            title="No applications found"
            description="Bookmarked or approved applications from the Jobs page will appear here."
          />
        )}

        {/* Applications Table */}
        {!isLoading && !isError && filteredApps.length > 0 && (
          <div className="w-full overflow-x-auto">
            <ApplicationTable
              applications={filteredApps}
              onSelectApplication={handleSelectApp}
              onUpdateStatus={handleUpdateStatus}
              onStartApply={handleStartApply}
            />
          </div>
        )}

        {/* Application Details Modal */}
        <Modal
          isOpen={isDetailModalOpen}
          onClose={() => setIsDetailModalOpen(false)}
          title="Application Overview"
          size="lg"
        >
          {selectedApp && (
            <ApplicationDetail
              application={selectedApp}
              onSaveNotes={handleSaveNotes}
              isSavingNotes={updateNotesMutation.isPending}
            />
          )}
        </Modal>

        {/* Automation Modal */}
        <Modal
          isOpen={isAutoModalOpen}
          onClose={() => setIsAutoModalOpen(false)}
          title="Playwright Application Assistant"
          size="lg"
        >
          {automationApp && (
            <AutomationModal
              application={automationApp}
              automationState={automationState}
              onStartAutomation={handleRunAutomation}
              onConfirmSubmit={handleConfirmSubmit}
              isStarting={startAutoMutation.isPending}
              isSubmitting={confirmSubmitMutation.isPending}
            />
          )}
        </Modal>
        </div>
      </PageWrapper>
    </>
  );
}

export default TrackerPage;
