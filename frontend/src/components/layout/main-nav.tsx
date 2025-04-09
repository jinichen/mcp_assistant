import React, { useState } from "react";
import { ThemeToggle } from "@/components/theme-toggle";
import { LanguageToggle } from "@/components/language-toggle";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { useAuth } from "@/context/auth-context";
import { useRouter } from "next/navigation";
import { useParams } from "next/navigation";
import { 
  User, 
  LogOut, 
  Settings,
  ChevronDown 
} from "lucide-react";
import { getDictionary } from "@/lib/dictionary";

interface MainNavProps {
  className?: string;
  dictionary: any;
}

export function MainNav({ className, dictionary }: MainNavProps) {
  const { isAuthenticated, logout, user } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const router = useRouter();
  const params = useParams();
  const lang = params?.lang || 'en';

  const handleLogout = () => {
    logout();
    setDropdownOpen(false);
    router.push(`/${lang}`);
  };

  const handleSettings = () => {
    setDropdownOpen(false);
    router.push(`/${lang}/settings`);
  };

  return (
    <header className={cn("h-14 flex items-center justify-end px-4", className)}>
      <div className="flex items-center gap-3">
        <LanguageToggle />
        <div className="h-5 w-px bg-primary/10"></div>
        <ThemeToggle />
        
        {isAuthenticated && (
          <>
            <div className="h-5 w-px bg-primary/10"></div>
            <div className="relative">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1.5 text-sm font-medium text-primary transition-colors hover:bg-primary/20"
              >
                <User size={16} />
                <span className="hidden sm:inline-block">{user?.username || 'User'}</span>
                <ChevronDown size={14} className={cn("transition-transform", dropdownOpen && "rotate-180")} />
              </button>
              
              {dropdownOpen && (
                <div className="absolute right-0 mt-1 w-36 rounded-md shadow-lg bg-popover border border-border overflow-hidden z-50">
                  <div className="py-1">
                    <button
                      onClick={handleSettings}
                      className="flex w-full items-center gap-2 px-4 py-2 text-sm hover:bg-muted transition-colors"
                    >
                      <Settings size={16} />
                      <span>{dictionary.layout.userProfile.settings}</span>
                    </button>
                    <button
                      onClick={handleLogout}
                      className="flex w-full items-center gap-2 px-4 py-2 text-sm text-destructive hover:bg-muted transition-colors"
                    >
                      <LogOut size={16} />
                      <span>{dictionary.layout.userProfile.logout}</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </header>
  );
} 