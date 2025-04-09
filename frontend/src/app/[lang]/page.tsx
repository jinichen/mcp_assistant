"use client";

import Link from "next/link";
import MainLayout from "@/components/layout/main-layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardTitle } from "@/components/ui/card";
import { MessageSquare, Settings, SparklesIcon, ArrowRight } from "lucide-react";
import { useParams } from "next/navigation";
import { getDictionary } from "@/lib/dictionary";

export default function HomePage() {
  // Get current language from route parameter
  const params = useParams();
  const lang = (params?.lang as string) || "en";
  const { home: t } = getDictionary(lang);
  
  return (
    <MainLayout dictionary={getDictionary(lang)}>
      <div className="container mx-auto px-4 py-6">
        <div className="flex flex-col h-full">
          <div className="flex flex-col items-center text-center space-y-4 py-5">
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight gradient-text">{t.welcome}</h1>
            <p className="text-sm md:text-base text-muted-foreground max-w-3xl">
              {t.subtitle}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl mx-auto flex-1 overflow-hidden">
            <div className="space-y-4 overflow-auto pr-3 mt-10">
              <h2 className="text-lg font-semibold gradient-text">{t.features}</h2>
              
              <Card className="elegant-card overflow-hidden group">
                <CardContent className="py-4 px-5">
                  <div className="flex items-start gap-4">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary group-hover:bg-primary/15 transition-colors duration-300">
                      <MessageSquare className="h-5 w-5 group-hover:scale-110 transition-transform duration-300" />
                    </div>
                    <div className="space-y-1">
                      <CardTitle className="text-base">{t.conversation.title}</CardTitle>
                      <CardDescription className="text-sm">
                        {t.conversation.description}
                      </CardDescription>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="elegant-card overflow-hidden group">
                <CardContent className="py-5 px-5">
                  <div className="flex items-start gap-4">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary group-hover:bg-primary/15 transition-colors duration-300">
                      <SparklesIcon className="h-5 w-5 group-hover:scale-110 transition-transform duration-300" />
                    </div>
                    <div className="space-y-1">
                      <CardTitle className="text-base">{t.multimodal.title}</CardTitle>
                      <CardDescription className="text-sm">
                        {t.multimodal.description}
                      </CardDescription>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="elegant-card overflow-hidden group">
                <CardContent className="py-5 px-5">
                  <div className="flex items-start gap-4">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary group-hover:bg-primary/15 transition-colors duration-300">
                      <Settings className="h-5 w-5 group-hover:scale-110 transition-transform duration-300" />
                    </div>
                    <div className="space-y-1">
                      <CardTitle className="text-base">{t.tools.title}</CardTitle>
                      <CardDescription className="text-sm">
                        {t.tools.description}
                      </CardDescription>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
            
            <div className="space-y-6 overflow-auto pl-3 mt-10">
              <Card className="elegant-card p-5 h-fit glass-effect">
                <h2 className="text-lg font-semibold mb-3 gradient-text">{t.startChat.title}</h2>
                <p className="text-sm text-muted-foreground mb-4">
                  {t.startChat.description}
                </p>
                <Link href={`/${lang}/chat`} className="block">
                  <Button className="w-full text-sm elegant-button group">
                    <MessageSquare className="mr-2 h-4 w-4 group-hover:animate-pulse" />
                    {t.startChat.button}
                    <ArrowRight className="ml-2 h-3 w-3 opacity-70 group-hover:translate-x-1 transition-transform" />
                  </Button>
                </Link>
              </Card>
              
              <Card className="elegant-card p-5 h-fit glass-effect">
                <h2 className="text-lg font-semibold mb-3 gradient-text">{t.settings.title}</h2>
                <p className="text-sm text-muted-foreground mb-4">
                  {t.settings.description}
                </p>
                <Link href={`/${lang}/settings`} className="block">
                  <Button variant="outline" className="w-full text-sm group">
                    <Settings className="mr-2 h-4 w-4 group-hover:rotate-45 transition-transform" />
                    {t.settings.button}
                    <ArrowRight className="ml-2 h-3 w-3 opacity-70 group-hover:translate-x-1 transition-transform" />
                  </Button>
                </Link>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
} 