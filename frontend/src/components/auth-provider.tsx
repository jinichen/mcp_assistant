"use client";

import React from "react";
import { AuthProvider as ContextProvider } from "@/context/auth-context";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  return <ContextProvider>{children}</ContextProvider>;
} 