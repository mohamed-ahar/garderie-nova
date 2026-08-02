"use client";

import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="bg-slate-50 dark:bg-darkBg text-slate-800 dark:text-slate-100 font-sans antialiased min-h-screen">
      <Sidebar isOpen={sidebarOpen} toggleSidebar={() => setSidebarOpen(!sidebarOpen)} />
      
      <div className={`lg:ml-72 min-h-screen transition-all duration-500 ease-in-out`}>
        <Header toggleSidebar={() => setSidebarOpen(!sidebarOpen)} />
        <main className="p-2 md:p-6 space-y-10 max-w-[1600px] mx-auto">
            {children}
        </main>
      </div>
    </div>
  );
}