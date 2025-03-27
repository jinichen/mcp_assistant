"use client";

import React from 'react';
import { Moon, Sun, Globe } from 'lucide-react';
import { useTheme } from 'next-themes';
import { Button } from '@/components/ui/button';
import { LanguageSwitcher } from './LanguageSwitcher';

interface TopNavProps {
  pageTitle: string;
}

export function TopNav({ pageTitle }: TopNavProps) {
  const { theme, setTheme } = useTheme();
  
  return (
    <div style={{
      height: '100%',
      padding: '0 16px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      boxShadow: '0 1px 2px rgba(0, 0, 0, 0.03)'
    }}>
      <h1 style={{
        fontSize: '18px',
        fontWeight: 600,
        color: '#111827'
      }}>
        {pageTitle}
      </h1>
      
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px'
      }}>
        {/* Language switcher */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px'
        }}>
          <Globe size={16} style={{ color: '#4b5563' }} />
          <LanguageSwitcher />
        </div>
        
        {/* Theme toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          style={{
            borderRadius: '50%',
            height: '32px',
            width: '32px',
            color: '#4b5563',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'background-color 0.2s',
            border: '1px solid transparent',
            marginLeft: '4px',
            padding: 0
          }}
        >
          {theme === 'dark' ? (
            <Sun size={18} />
          ) : (
            <Moon size={18} />
          )}
        </Button>
      </div>
    </div>
  );
}

export default TopNav; 