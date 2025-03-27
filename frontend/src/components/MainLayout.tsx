"use client";

import { ReactNode } from "react";
import { Sidebar } from "@/components/Sidebar";
import { TopNav } from "@/components/TopNav";
import { Toaster } from "sonner";

interface MainLayoutProps {
  children: ReactNode;
  activePage: 'home' | 'chat' | 'settings';
  pageTitle: string;
}

export default function MainLayout({ children, activePage, pageTitle }: MainLayoutProps) {
  return (
    <div className="h-screen flex flex-row" style={{ backgroundColor: 'white', maxHeight: '100vh', overflow: 'hidden' }}>
      {/* Left sidebar - fixed width */}
      <div className="h-full w-56 border-r" style={{ borderColor: '#e5e7eb' }}>
        <Sidebar activePage={activePage} />
      </div>

      {/* Right content area - flexible width */}
      <div className="flex flex-col flex-1 h-full">
        {/* Top navigation */}
        <header className="h-14 border-b" style={{ borderColor: '#e5e7eb' }}>
          <TopNav pageTitle={pageTitle} />
        </header>
        
        {/* Main content */}
        <main className="flex-1 p-3 overflow-hidden">
          {children}
        </main>
      </div>
      
      <Toaster position="bottom-right" />
    </div>
  );
} 