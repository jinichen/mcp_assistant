"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";

interface AuthContextType {
  token: string | null;
  user: any | null;
  isAuthenticated: boolean;
  login: (token: string, user: any) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Helper function: Check if token is valid
const isTokenValid = (token: string): boolean => {
  try {
    // Simple check if token format is correct (JWT format: xxx.yyy.zzz)
    if (!token || typeof token !== 'string' || !token.includes('.')) {
      return false;
    }
    
    // Try to decode JWT payload (second part) to check expiration time
    const payload = JSON.parse(atob(token.split('.')[1]));
    
    // Check if token is expired
    if (payload.exp && payload.exp * 1000 < Date.now()) {
      console.log('Token has expired');
      return false;
    }
    
    return true;
  } catch (error) {
    console.error('Error validating token:', error);
    return false;
  }
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<any | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check if there's a token in localStorage and validate it
    if (typeof window !== 'undefined') {
      const storedToken = localStorage.getItem("token");
      const storedUser = localStorage.getItem("user");
      
      if (storedToken && isTokenValid(storedToken)) {
        setToken(storedToken);
        setIsAuthenticated(true);
        
        if (storedUser) {
          try {
            setUser(JSON.parse(storedUser));
          } catch (error) {
            console.error("Failed to parse user data:", error);
          }
        }
      } else if (storedToken) {
        // If token exists but is invalid, clear localStorage
        console.log('Invalid token found, logging out');
        localStorage.removeItem("token");
        localStorage.removeItem("user");
      }
    }
  }, []);

  const login = (newToken: string, userData: any) => {
    if (!isTokenValid(newToken)) {
      console.error('Attempted to login with invalid token');
      return;
    }
    
    setToken(newToken);
    setUser(userData);
    setIsAuthenticated(true);
    
    // Store in localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem("token", newToken);
      localStorage.setItem("user", JSON.stringify(userData));
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
    
    // Clear localStorage
    if (typeof window !== 'undefined') {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
    }
  };

  return (
    <AuthContext.Provider value={{ token, user, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
} 