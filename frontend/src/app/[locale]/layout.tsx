"use client";

import { NextIntlClientProvider } from 'next-intl';
import { notFound } from 'next/navigation';
import { useEffect, useState, use } from 'react';
import { locales } from '../../i18n';

type Props = {
  children: React.ReactNode;
  params: { locale: string } | Promise<{ locale: string }>;
};

export default function LocaleLayout({ children, params }: Props) {
  // Use React.use() to unwrap the params Promise
  const unwrappedParams = use(params as Promise<{ locale: string }>);
  const locale = unwrappedParams.locale;
  
  const [messages, setMessages] = useState<Record<string, string> | null>(null);
  
  useEffect(() => {
    if (!locales.includes(locale)) {
      notFound();
    }

    // Load messages
    import(`../../messages/${locale}.json`)
      .then((module) => {
        setMessages(module.default);
      })
      .catch(() => {
        notFound();
      });
  }, [locale]);

  // Show a loading state while messages are loading
  if (!messages) {
    return (
      <div style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "100vh",
        width: "100%",
        background: "linear-gradient(to bottom right, #f8fafc, #e0f2fe)"
      }}>
        <div style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "20px"
        }}>
          <div style={{
            width: "80px",
            height: "80px",
            border: "4px solid #e5e7eb",
            borderTopColor: "#3b82f6",
            borderRadius: "50%",
            animation: "spin 1s linear infinite"
          }} />
          <p style={{
            fontSize: "18px",
            fontWeight: "500",
            color: "#1e3a8a"
          }}>
            {locale === 'zh-CN' ? '加载中...' : 'Loading...'}
          </p>
          <style jsx global>{`
            @keyframes spin {
              to { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      </div>
    );
  }

  return (
    <NextIntlClientProvider locale={locale} messages={messages}>
      {children}
    </NextIntlClientProvider>
  );
} 