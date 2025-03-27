"use client";

import React, { useState } from 'react';
import { Home, MessageSquare, Settings, ChevronRight } from 'lucide-react';
import Link from 'next/link';
import { usePathname, useParams } from 'next/navigation';

interface SidebarProps {
  activePage: 'home' | 'chat' | 'settings';
}

export function Sidebar({ activePage }: SidebarProps) {
  const pathname = usePathname();
  const params = useParams();
  const locale = Array.isArray(params.locale) ? params.locale[0] : params.locale as string;
  
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);
  
  const linkStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '8px 16px',
    marginBottom: '4px',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: 500,
    transition: 'all 0.2s ease',
    position: 'relative' as const
  };
  
  const activeLinkStyle = {
    ...linkStyle,
    backgroundColor: '#ebf5ff',
    color: '#2563eb',
    boxShadow: '0 1px 3px rgba(37, 99, 235, 0.1)'
  };
  
  const inactiveLinkStyle = {
    ...linkStyle,
    color: '#4b5563',
    backgroundColor: 'transparent'
  };
  
  const hoverIndicatorStyle = {
    position: 'absolute' as const,
    right: '12px',
    opacity: 0.7
  };
  
  const isActive = (path: string) => {
    const currentPath = `/${locale}${path}`;
    return pathname === currentPath;
  };
  
  return (
    <div className="h-full flex flex-col" style={{ 
      backgroundColor: 'white',
      background: 'linear-gradient(to bottom, white, #f8fafc)'
    }}>
      {/* Logo section */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '56px',
        borderBottom: '1px solid #e5e7eb',
        background: 'linear-gradient(135deg, #f0f9ff, #e0f2fe)'
      }}>
        <Link href={`/${locale}`} style={{ 
          fontSize: '20px', 
          fontWeight: 'bold', 
          color: '#2563eb',
          letterSpacing: '-0.02em',
          background: 'linear-gradient(to right, #2563eb, #60a5fa)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          ASA
        </Link>
      </div>

      {/* Navigation */}
      <nav style={{ padding: '16px 12px', flex: 1 }}>
        <Link
          href={`/${locale}`}
          style={isActive('') ? activeLinkStyle : inactiveLinkStyle}
          onMouseEnter={() => setHoveredItem('home')}
          onMouseLeave={() => setHoveredItem(null)}
        >
          <Home size={16} style={{ color: isActive('') ? '#2563eb' : '#6b7280' }} />
          <span>{locale === 'zh-CN' ? '首页' : 'Home'}</span>
          {hoveredItem === 'home' && !isActive('') && (
            <ChevronRight size={14} style={hoverIndicatorStyle} />
          )}
        </Link>
        <Link
          href={`/${locale}/chat`}
          style={isActive('/chat') ? activeLinkStyle : inactiveLinkStyle}
          onMouseEnter={() => setHoveredItem('chat')}
          onMouseLeave={() => setHoveredItem(null)}
        >
          <MessageSquare size={16} style={{ color: isActive('/chat') ? '#2563eb' : '#6b7280' }} />
          <span>{locale === 'zh-CN' ? '对话' : 'Chat'}</span>
          {hoveredItem === 'chat' && !isActive('/chat') && (
            <ChevronRight size={14} style={hoverIndicatorStyle} />
          )}
        </Link>
        <Link
          href={`/${locale}/settings`}
          style={isActive('/settings') ? activeLinkStyle : inactiveLinkStyle}
          onMouseEnter={() => setHoveredItem('settings')}
          onMouseLeave={() => setHoveredItem(null)}
        >
          <Settings size={16} style={{ color: isActive('/settings') ? '#2563eb' : '#6b7280' }} />
          <span>{locale === 'zh-CN' ? '设置' : 'Settings'}</span>
          {hoveredItem === 'settings' && !isActive('/settings') && (
            <ChevronRight size={14} style={hoverIndicatorStyle} />
          )}
        </Link>
      </nav>

      {/* Version info at the bottom */}
      <div style={{
        padding: '12px 16px',
        marginTop: 'auto',
        borderTop: '1px solid #e5e7eb',
        fontSize: '12px',
        color: '#6b7280',
        fontWeight: '500',
        background: 'linear-gradient(to bottom, rgba(248, 250, 252, 0), rgba(248, 250, 252, 1))'
      }}>
        AI Assistant v0.1
      </div>
    </div>
  );
}

export default Sidebar; 