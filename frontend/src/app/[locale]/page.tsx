"use client"

import React from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowRight, Sparkles, LifeBuoy, Zap, MessageSquare, Settings } from 'lucide-react';
import MainLayout from '@/components/MainLayout';
import { Button } from '@/components/ui/button';
import Image from 'next/image';
import { Wrench } from 'lucide-react';

export default function HomePage() {
  const params = useParams();
  const locale = Array.isArray(params.locale) ? params.locale[0] : params.locale as string;
  
  const iconStyle = {
    width: '24px',
    height: '24px',
    color: '#4b70a8'
  };
  
  return (
    <MainLayout activePage="home" pageTitle={locale === 'zh-CN' ? '首页' : 'Home'}>
      <div className="container mx-auto">
        <div 
          style={{ 
            minHeight: 'calc(100vh - 130px)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center'
          }}
        >
          <header className="mb-12 text-center">
            <h1 className="text-4xl font-bold mb-4" style={{ color: '#2d4a7e' }}>
              {locale === 'zh-CN' ? '欢迎使用 ASA 智能助手' : 'Welcome to ASA AI Assistant'}
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              {locale === 'zh-CN' 
                ? '基于模型上下文协议（MCP）的智能AI助手，支持多模态交互和工具使用' 
                : 'An intelligent AI assistant based on Model Context Protocol (MCP), supporting multimodal interactions and tool usage'
              }
            </p>
          </header>
          
          {/* Main content area - two column layout */}
          <div className="grid md:grid-cols-2 gap-16 px-4 max-w-6xl mx-auto">
            
            {/* Left text area */}
            <div className="flex flex-col justify-center">
              <h2 className="text-2xl font-semibold mb-6 text-indigo-600">
                {locale === 'zh-CN' ? '主要功能' : 'Key Features'}
              </h2>
              
              <ul className="space-y-6">
                <li className="flex items-start">
                  <div className="mr-4 p-2 bg-blue-50 rounded-lg">
                    <MessageSquare style={iconStyle} />
                  </div>
                  <div>
                    <h3 className="font-medium text-lg text-gray-800 mb-1">
                      {locale === 'zh-CN' ? '自然语言对话' : 'Natural Language Conversations'}
                    </h3>
                    <p className="text-gray-600">
                      {locale === 'zh-CN'
                        ? '与先进的AI模型进行自然、流畅的对话交流'
                        : 'Engage in natural, fluid conversations with advanced AI models'
                      }
                    </p>
                  </div>
                </li>
                
                <li className="flex items-start">
                  <div className="mr-4 p-2 bg-blue-50 rounded-lg">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4b70a8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect width="18" height="18" x="3" y="3" rx="2" ry="2" />
                      <circle cx="9" cy="9" r="2" />
                      <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-medium text-lg text-gray-800 mb-1">
                      {locale === 'zh-CN' ? '多模态能力' : 'Multimodal Capabilities'}
                    </h3>
                    <p className="text-gray-600">
                      {locale === 'zh-CN'
                        ? '支持图像分析和理解，实现视觉和文本的结合交互'
                        : 'Supports image analysis and understanding, enabling combined visual and textual interactions'
                      }
                    </p>
                  </div>
                </li>
                
                <li className="flex items-start">
                  <div className="mr-4 p-2 bg-blue-50 rounded-lg">
                    <Wrench style={iconStyle} />
                  </div>
                  <div>
                    <h3 className="font-medium text-lg text-gray-800 mb-1">
                      {locale === 'zh-CN' ? '工具使用' : 'Tool Usage'}
                    </h3>
                    <p className="text-gray-600">
                      {locale === 'zh-CN'
                        ? 'AI可以使用外部工具和API来完成复杂任务'
                        : 'AI can use external tools and APIs to complete complex tasks'
                      }
                    </p>
                  </div>
                </li>
              </ul>
            </div>
            
            {/* Right feature cards */}
            <div className="flex flex-col justify-center">
              <div className="bg-white rounded-xl shadow-md p-6 mb-6 border border-gray-100 transform transition-all hover:scale-105">
                <h3 className="font-semibold text-xl mb-3 text-blue-600">
                  {locale === 'zh-CN' ? '开始对话' : 'Start a Conversation'}
                </h3>
                <p className="text-gray-600 mb-4">
                  {locale === 'zh-CN'
                    ? '前往聊天页面，开始与AI助手交流'
                    : 'Head to the chat page to start interacting with the AI assistant'
                  }
                </p>
                <Link 
                  href={`/${locale}/chat`}
                  className="inline-flex items-center justify-center bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
                >
                  <MessageSquare className="mr-2 h-4 w-4" />
                  {locale === 'zh-CN' ? '开始聊天' : 'Start Chatting'}
                </Link>
              </div>
              
              <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100 transform transition-all hover:scale-105">
                <h3 className="font-semibold text-xl mb-3 text-indigo-600">
                  {locale === 'zh-CN' ? '自定义设置' : 'Customize Settings'}
                </h3>
                <p className="text-gray-600 mb-4">
                  {locale === 'zh-CN'
                    ? '调整应用设置，选择您偏好的AI模型和界面主题'
                    : 'Adjust application settings, choose your preferred AI model and interface theme'
                  }
                </p>
                <Link 
                  href={`/${locale}/settings`}
                  className="inline-flex items-center justify-center bg-indigo-500 text-white px-4 py-2 rounded-lg hover:bg-indigo-600 transition-colors"
                >
                  <Settings className="mr-2 h-4 w-4" />
                  {locale === 'zh-CN' ? '前往设置' : 'Go to Settings'}
                </Link>
              </div>
            </div>
            
          </div>
        </div>
      </div>
    </MainLayout>
  );
} 