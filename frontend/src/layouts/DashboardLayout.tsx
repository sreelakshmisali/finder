import { Outlet } from "react-router-dom";

function DashboardLayout() {
  return (
    <div className="min-h-screen bg-bg selection:bg-primary-muted selection:text-white">
      <main className="min-h-screen flex flex-col relative max-w-full overflow-x-hidden">
        <Outlet />
      </main>
    </div>
  );
}

export default DashboardLayout;
