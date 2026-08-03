"use client";

import { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import { AuthProvider } from "@/context/AuthContext";

function DashboardContent({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    const savedState = localStorage.getItem('sidebarOpen');
    if (savedState !== null) {
      setSidebarOpen(JSON.parse(savedState));
    }
  }, []);

  const handleSidebarToggle = () => {
    const newState = !sidebarOpen;
    setSidebarOpen(newState);
    localStorage.setItem('sidebarOpen', JSON.stringify(newState));
  };

  return (
    <div className="bg-slate-50 dark:bg-darkBg text-slate-800 dark:text-slate-100 font-sans antialiased min-h-screen">
      <Sidebar isOpen={sidebarOpen} toggleSidebar={handleSidebarToggle} />
      
      <div className={`${sidebarOpen ? 'lg:ml-72' : 'lg:ml-0'} min-h-screen transition-all duration-500 ease-in-out`}>
        <Header toggleSidebar={handleSidebarToggle} />
        <main className="p-2 md:p-6 space-y-10 max-w-[1600px] mx-auto">
            {children}
        </main>
      </div>
    </div>
  );
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <DashboardContent>{children}</DashboardContent>
    </AuthProvider>
  );
}