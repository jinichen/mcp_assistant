"use client";

import { usePathname, useRouter } from 'next/navigation';
import { useParams } from 'next/navigation';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { locales } from '@/i18n';

export function LanguageSwitcher() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useParams();
  const currentLocale = Array.isArray(params.locale) ? params.locale[0] : params.locale as string;

  const handleLocaleChange = (newLocale: string) => {
    // Get the path without the locale
    const pathWithoutLocale = pathname.replace(`/${currentLocale}`, '');
    
    // Construct the new path with the new locale
    const newPath = `/${newLocale}${pathWithoutLocale}`;
    
    // Navigate to the new path
    router.push(newPath);
  };

  const getLanguageName = (locale: string) => {
    switch (locale) {
      case 'en':
        return 'EN';
      case 'zh-CN':
        return '中文';
      default:
        return locale;
    }
  };

  return (
    <div style={{ 
      display: 'flex', 
      alignItems: 'center'
    }}>
      <Select value={currentLocale} onValueChange={handleLocaleChange}>
        <SelectTrigger style={{ 
          width: '90px',
          border: '2px solid #2563eb',
          borderRadius: '8px',
          padding: '2px 12px 2px 16px',
          fontSize: '16px',
          backgroundColor: '#2563eb',
          color: 'white',
          height: '36px',
          fontWeight: '600',
          boxShadow: '0 2px 4px rgba(37, 99, 235, 0.3)',
        }}>
          <SelectValue>{getLanguageName(currentLocale)}</SelectValue>
        </SelectTrigger>
        <SelectContent className="p-0 overflow-hidden" style={{
          backgroundColor: '#ffffff',
          border: '2px solid #2563eb',
          borderRadius: '8px',
          boxShadow: '0 6px 16px rgba(0, 0, 0, 0.15)',
          overflow: 'hidden',
          minWidth: '120px',
          transform: 'translateY(4px)'
        }}>
          <div style={{ padding: '4px' }}>
            {locales.map((locale, index) => (
              <div
                key={locale}
                style={{
                  padding: '8px 12px',
                  backgroundColor: locale === currentLocale ? '#dbeafe' : 'white',
                  color: locale === currentLocale ? '#1e3a8a' : '#1f2937',
                  fontWeight: locale === currentLocale ? '600' : '500',
                  fontSize: '15px',
                  cursor: 'pointer',
                  borderRadius: '4px',
                  marginBottom: index < locales.length - 1 ? '2px' : '0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'all 0.2s ease'
                }}
                onClick={() => handleLocaleChange(locale)}
              >
                {getLanguageName(locale)}
                {locale === currentLocale && (
                  <span style={{ 
                    marginLeft: '8px', 
                    color: '#2563eb',
                    fontSize: '14px'
                  }}>✓</span>
                )}
              </div>
            ))}
          </div>
        </SelectContent>
      </Select>
    </div>
  );
} 