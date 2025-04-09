"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useParams } from "next/navigation";
import { Home, MessageSquare, Settings } from "lucide-react";
import { cn } from "@/lib/utils";
import { getDictionary } from "@/lib/dictionary";

interface SidebarProps {
  className?: string;
}

export function Sidebar({ className }: SidebarProps) {
  const pathname = usePathname();
  const params = useParams();
  const lang = (params?.lang as string) || "en";
  const { layout } = getDictionary(lang);
  
  // Extract the base path (without language prefix)
  const basePath = pathname.replace(/^\/(en|zh)/, "");
  
  const navigation = [
    { name: layout.home, href: `/${lang}`, icon: Home },
    { name: layout.chat, href: `/${lang}/chat`, icon: MessageSquare },
    { name: layout.settings, href: `/${lang}/settings`, icon: Settings },
  ];

  return (
    <div className={cn("w-60 h-full bg-card/50 backdrop-blur-sm", className)}>
      <div className="h-14 flex items-center justify-center border-b border-primary/10">
        <h1 className="text-5xl font-bold bg-gradient-to-r from-primary to-indigo-500 text-transparent bg-clip-text">
          ASA
        </h1>
      </div>
      <nav className="px-2 py-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center px-3 py-2 text-sm font-medium rounded-md transition-all group",
                isActive
                  ? "bg-primary/10 text-primary shadow-sm"
                  : "text-muted-foreground hover:bg-primary/5 hover:text-foreground"
              )}
            >
              <item.icon
                className={cn(
                  "mr-3 h-5 w-5 transition-colors",
                  isActive
                    ? "text-primary"
                    : "text-muted-foreground group-hover:text-foreground"
                )}
              />
              {item.name}
            </Link>
          );
        })}
      </nav>
      <div className="absolute bottom-4 left-0 right-0 px-5">
        <div className="p-3 rounded-lg bg-muted/50 border border-primary/5 shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="h-8 w-8 rounded-full bg-gradient-to-r from-primary/20 to-indigo-500/20 flex items-center justify-center">
              <MessageSquare className="h-4 w-4 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-foreground">
                {layout.assistantReady}
              </p>
              <p className="text-xs text-muted-foreground truncate">
                {layout.assistantDesc}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 