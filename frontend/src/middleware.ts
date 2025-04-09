import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Supported languages
const supportedLocales = ["en", "zh"];
// Default language
const defaultLocale = "en";

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  
  // Check if URL already has a language prefix
  const pathnameHasLocale = supportedLocales.some(
    (locale) => pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`
  );

  if (pathnameHasLocale) return NextResponse.next();
  
  // Check preferred language in cookies
  const cookieLocale = request.cookies.get("NEXT_LOCALE")?.value;
  
  // Get user's preferred language from Accept-Language header
  const acceptLanguage = request.headers.get("accept-language");
  let userLocale = defaultLocale;
  
  if (acceptLanguage) {
    const parsedLocales = acceptLanguage.split(",").map((l) => {
      const [locale, q = "1"] = l.trim().split(";q=");
      return { locale: locale.split("-")[0], q: parseFloat(q) };
    });
    
    // Sort by q value
    parsedLocales.sort((a, b) => b.q - a.q);
    
    // Find the first supported language
    for (const { locale } of parsedLocales) {
      if (supportedLocales.includes(locale)) {
        userLocale = locale;
        break;
      }
    }
  }
  
  // Determine language to use: prioritize cookie, then Accept-Language, finally default value
  const locale = cookieLocale && supportedLocales.includes(cookieLocale)
    ? cookieLocale
    : userLocale;
  
  // Build new URL
  const newUrl = new URL(`/${locale}${pathname}`, request.url);
  newUrl.search = request.nextUrl.search;
  
  return NextResponse.redirect(newUrl);
}

// Match all paths except specific exceptions (like static files)
export const config = {
  matcher: [
    "/((?!api|_next/static|_next/image|favicon.ico|.*\\.png$|.*\\.svg$).*)",
  ],
}; 