"use client"

import { ThemeProvider as NextThemesProvider } from "next-themes"
 
export function ThemeProvider({ children, ...props }: React.PropsWithChildren<any>) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>
} 