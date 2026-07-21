import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "../components/layout/Sidebar";

function DashboardLayout() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const handleToggle = () => setIsSidebarOpen(!isSidebarOpen);
  const handleClose = () => setIsSidebarOpen(false);

  return (
    <div className="flex min-h-screen bg-bg selection:bg-primary-muted selection:text-white">
      <Sidebar 
        isOpen={isSidebarOpen} 
        onClose={handleClose} 
        onToggle={handleToggle}
      />
      <main className="flex-1 md:ml-[240px] min-h-screen flex flex-col relative max-w-full overflow-x-hidden">
        <Outlet context={{ onMenuClick: handleToggle }} />
      </main>
    </div>
  );
}

export default DashboardLayout;
