"use client";

import { useRouter } from "next/navigation";
import { usePathname, useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Globe } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { getDictionary } from "@/lib/dictionary";

const languages = [
  { code: "en", label: "English" },
  { code: "zh", label: "中文" },
];

export function LanguageToggle() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useParams();
  const lang = (params?.lang as string) || "en";
  const { layout: t } = getDictionary(lang);
  
  // Simple language detection from path
  const currentLang = pathname.split("/")[1] || "en";
  
  const switchLanguage = (langCode: string) => {
    // Remove the current language from the path
    const newPathname = pathname.replace(/^\/(en|zh)/, "");
    router.push(`/${langCode}${newPathname}`);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" title={t.header.languageToggle}>
          <Globe className="h-5 w-5" />
          <span className="sr-only">{t.header.languageToggle}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {languages.map((lang) => (
          <DropdownMenuItem
            key={lang.code}
            onClick={() => switchLanguage(lang.code)}
            className={currentLang === lang.code ? "bg-primary/10" : ""}
          >
            {lang.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
} 