import {notFound} from 'next/navigation';
import {getRequestConfig} from 'next-intl/server';

// Define supported languages
export const locales = ['en', 'zh-CN'];
export const defaultLocale = 'en';

// Configure internationalization
export default getRequestConfig(async ({locale}) => {
  // Validate locale to ensure it's supported
  if (!locales.includes(locale)) {
    notFound();
  }

  // Load messages for the current locale
  // Using dynamic import to load only the required language file
  try {
    return {
      messages: (await import(`./messages/${locale}.json`)).default
    };
  } catch (error) {
    console.error(`Failed to load messages for locale: ${locale}`, error);
    // Fallback to default locale in case of error
    return {
      messages: (await import(`./messages/${defaultLocale}.json`)).default
    };
  }
}); 