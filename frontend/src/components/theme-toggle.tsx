"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { useParams } from "next/navigation";
import { getDictionary } from "@/lib/dictionary";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const params = useParams();
  const lang = (params?.lang as string) || "en";
  const { layout: t } = getDictionary(lang);

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      title={t.header.themeToggle}
    >
      <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
      <span className="sr-only">{t.header.themeToggle}</span>
    </Button>
  );
} 