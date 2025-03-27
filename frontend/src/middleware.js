import createMiddleware from 'next-intl/middleware';
import {locales, defaultLocale} from './i18n';

// This middleware intercepts requests and redirects to the appropriate locale
export default createMiddleware({
  // A list of all locales that are supported
  locales,
  
  // Default locale to use when no locale matches
  defaultLocale,
  
  // Always include the locale in the URL
  localePrefix: 'always'
});

export const config = {
  // Match all paths except for:
  // - API routes: /api/*
  // - Static files: /_next/* and other static assets
  matcher: ['/((?!api|_next|_vercel|.*\\..*).*)']
}; 