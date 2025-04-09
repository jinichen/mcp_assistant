"use client";

import { useState } from "react";
import MainLayout from "@/components/layout/main-layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { InfoIcon, Check } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useParams } from "next/navigation";
import { getDictionary } from "@/lib/dictionary";

export default function SettingsPage() {
  // Get current language from route parameter
  const params = useParams();
  const lang = (params?.lang as string) || "en";
  const { settings: t } = getDictionary(lang);

  const [streamResponses, setStreamResponses] = useState(true);
  const [saveChatHistory, setSaveChatHistory] = useState(true);
  const [usageAnalytics, setUsageAnalytics] = useState(true);
  const [themeMode, setThemeMode] = useState("system");

  return (
    <MainLayout dictionary={getDictionary(lang)}>
      <div className="space-y-8 max-w-4xl mx-auto">
        <section>
          <h2 className="text-2xl font-semibold mb-4">{t.appearance.title}</h2>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">{t.appearance.subtitle}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="theme-mode">{t.appearance.themeMode}</Label>
                  <Select value={themeMode} onValueChange={setThemeMode}>
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Select theme" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="light">{t.appearance.light}</SelectItem>
                      <SelectItem value="dark">{t.appearance.dark}</SelectItem>
                      <SelectItem value="system">{t.appearance.system}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">{t.model.title}</h2>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">{t.model.subtitle}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border p-4 flex items-start gap-4">
                <InfoIcon className="h-5 w-5 text-blue-500 mt-0.5" />
                <div>
                  <h3 className="font-medium">{t.model.fixedModel}</h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    {t.model.description}
                  </p>
                  
                  <div className="mt-4 rounded-md border p-3 bg-muted/50">
                    <p className="text-sm font-medium">{t.model.currentModel} <span className="text-blue-500">{t.model.modelNotLoaded}</span></p>
                  </div>
                  
                  <div className="mt-4">
                    <div className="flex items-center space-x-2">
                      <Switch 
                        id="stream-responses"
                        checked={streamResponses}
                        onCheckedChange={setStreamResponses}
                      />
                      <Label htmlFor="stream-responses">{t.model.streamResponses}</Label>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">{t.model.streamDescription}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">{t.privacy.title}</h2>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">{t.privacy.subtitle}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="save-chat-history">{t.privacy.saveChat}</Label>
                  <p className="text-xs text-muted-foreground mt-1">{t.privacy.saveChatDescription}</p>
                </div>
                <Switch 
                  id="save-chat-history"
                  checked={saveChatHistory}
                  onCheckedChange={setSaveChatHistory}
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="usage-analytics">{t.privacy.analytics}</Label>
                  <p className="text-xs text-muted-foreground mt-1">{t.privacy.analyticsDescription}</p>
                </div>
                <Switch 
                  id="usage-analytics"
                  checked={usageAnalytics}
                  onCheckedChange={setUsageAnalytics}
                />
              </div>
            </CardContent>
          </Card>
        </section>
        
        <div className="flex justify-end mb-8">
          <Button>
            <Check className="mr-2 h-4 w-4" />
            {t.saveButton}
          </Button>
        </div>
      </div>
    </MainLayout>
  );
} 