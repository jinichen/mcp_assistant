"use client";

import React from "react";
import { MainNav } from "@/components/layout/main-nav";
import { Sidebar } from "@/components/layout/sidebar";
import { ThemeToggle } from "@/components/theme-toggle";
import { LanguageToggle } from "@/components/language-toggle";

interface MainLayoutProps {
  children: React.ReactNode;
  dictionary: any;
}

export default function MainLayout({ children, dictionary }: MainLayoutProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 transition-all duration-500">
      {/* Main section with sidebar and content */}
      <div className="flex">
        {/* Sidebar */}
        <Sidebar className="fixed inset-y-0 z-30 transition-all duration-300 border-r border-primary/10 shadow-sm shadow-primary/5" />

        {/* Main content */}
        <div className="flex-1 ml-[240px] h-screen overflow-hidden">
          {/* Top navigation */}
          <MainNav dictionary={dictionary} className="sticky top-0 z-20 border-b border-primary/10 bg-background/80 backdrop-blur-sm shadow-sm" />
          
          {/* Page content */}
          <main className="flex-1 transition-all duration-300 page-transition-enter page-transition-enter-active h-[calc(100vh-4rem)]">
            <div className="max-w-7xl mx-auto h-full">
              {children}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
} 