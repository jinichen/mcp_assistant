"use client"

import React, { useState } from 'react';
import MainLayout from '@/components/MainLayout';
import { Card, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { useParams } from 'next/navigation';

export default function SettingsPage() {
  // Get current language
  const params = useParams();
  const locale = Array.isArray(params.locale) ? params.locale[0] : params.locale as string;
  
  // Switch states
  const [streamingEnabled, setStreamingEnabled] = useState(true);
  const [saveHistoryEnabled, setSaveHistoryEnabled] = useState(true);
  const [analyticsEnabled, setAnalyticsEnabled] = useState(true);

  return (
    <MainLayout activePage="settings" pageTitle={locale === 'zh-CN' ? '设置' : 'Settings'}>
      <div className="container mx-auto py-2" style={{ maxHeight: 'calc(100vh - 70px)', overflow: 'auto' }}>
        <div className="max-w-4xl mx-auto">
          {/* Appearance section */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-blue-600 mb-1">
              {locale === 'zh-CN' ? '外观' : 'Appearance'}
            </h3>
            <p className="text-xs text-gray-500 mb-3">
              {locale === 'zh-CN' ? '自定义应用的外观' : 'Customize the look'}
            </p>
            
            <div className="bg-blue-50 rounded-lg overflow-hidden border border-blue-100">
              <div className="flex items-center justify-between p-4">
                <div>
                  <Label className="text-sm font-medium text-gray-700">
                    {locale === 'zh-CN' ? '主题模式' : 'Theme Mode'}
                  </Label>
                </div>
                <Select defaultValue="system">
                  <SelectTrigger className="w-40 h-9 backdrop-filter backdrop-blur-md bg-white/70 border border-blue-200 hover:border-blue-300 text-gray-800 shadow-sm rounded-md font-medium">
                    <SelectValue placeholder={locale === 'zh-CN' ? '选择主题' : 'Select theme'} />
                  </SelectTrigger>
                  <SelectContent className="backdrop-filter backdrop-blur-md bg-white/80 border border-blue-200 shadow-lg rounded-md">
                    <SelectItem value="light">{locale === 'zh-CN' ? '浅色' : 'Light'}</SelectItem>
                    <SelectItem value="dark">{locale === 'zh-CN' ? '深色' : 'Dark'}</SelectItem>
                    <SelectItem value="system">{locale === 'zh-CN' ? '系统' : 'System'}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          
          {/* AI Model Settings section */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-indigo-600 mb-1">
              {locale === 'zh-CN' ? 'AI 模型设置' : 'AI Model Settings'}
            </h3>
            <p className="text-xs text-gray-500 mb-3">
              {locale === 'zh-CN' ? '配置 AI 模型偏好' : 'Configure AI model preferences'}
            </p>
            
            <div className="bg-blue-50 rounded-lg overflow-hidden border border-blue-100">
              <div className="flex items-center justify-between p-4 border-b border-blue-100">
                <div>
                  <Label className="text-sm font-medium text-gray-700">
                    {locale === 'zh-CN' ? '默认模型' : 'Default Model'}
                  </Label>
                </div>
                <Select defaultValue="google-gemini">
                  <SelectTrigger className="w-40 h-9 backdrop-filter backdrop-blur-md bg-white/70 border border-blue-200 hover:border-blue-300 text-gray-800 shadow-sm rounded-md font-medium">
                    <SelectValue placeholder={locale === 'zh-CN' ? '选择模型' : 'Select model'} />
                  </SelectTrigger>
                  <SelectContent className="backdrop-filter backdrop-blur-md bg-white/80 border border-blue-200 shadow-lg rounded-md">
                    <SelectItem value="google-gemini">Gemini Pro</SelectItem>
                    <SelectItem value="openai-gpt4">GPT-4</SelectItem>
                    <SelectItem value="anthropic-claude">Claude 3</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="flex items-center justify-between p-4">
                <div>
                  <Label htmlFor="streaming" className="text-sm font-medium text-gray-700">
                    {locale === 'zh-CN' ? '流式响应' : 'Stream Responses'}
                  </Label>
                  <p className="text-xs text-gray-500">
                    {locale === 'zh-CN' ? '实时显示生成内容' : 'Display responses in real-time'}
                  </p>
                </div>
                <div className="flex items-center">
                  <div 
                    className={`flex items-center justify-center w-16 h-8 rounded-md font-medium text-sm ${
                      streamingEnabled 
                        ? 'bg-indigo-600 text-white' 
                        : 'bg-gray-200 text-gray-500'
                    }`}
                    onClick={() => setStreamingEnabled(!streamingEnabled)}
                    style={{ cursor: 'pointer' }}
                  >
                    {locale === 'zh-CN' 
                      ? (streamingEnabled ? '开启' : '关闭') 
                      : (streamingEnabled ? 'ON' : 'OFF')
                    }
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Privacy & Data section */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-purple-600 mb-1">
              {locale === 'zh-CN' ? '隐私与数据' : 'Privacy & Data'}
            </h3>
            <p className="text-xs text-gray-500 mb-3">
              {locale === 'zh-CN' ? '管理数据和隐私偏好' : 'Manage data and privacy preferences'}
            </p>
            
            <div className="bg-blue-50 rounded-lg overflow-hidden border border-blue-100">
              <div className="flex items-center justify-between p-4 border-b border-blue-100">
                <div>
                  <Label htmlFor="save-history" className="text-sm font-medium text-gray-700">
                    {locale === 'zh-CN' ? '保存聊天历史' : 'Save Chat History'}
                  </Label>
                  <p className="text-xs text-gray-500">
                    {locale === 'zh-CN' ? '保留对话记录' : 'Keep conversation records'}
                  </p>
                </div>
                <div className="flex items-center">
                  <div 
                    className={`flex items-center justify-center w-16 h-8 rounded-md font-medium text-sm ${
                      saveHistoryEnabled 
                        ? 'bg-indigo-600 text-white' 
                        : 'bg-gray-200 text-gray-500'
                    }`}
                    onClick={() => setSaveHistoryEnabled(!saveHistoryEnabled)}
                    style={{ cursor: 'pointer' }}
                  >
                    {locale === 'zh-CN' 
                      ? (saveHistoryEnabled ? '开启' : '关闭') 
                      : (saveHistoryEnabled ? 'ON' : 'OFF')
                    }
                  </div>
                </div>
              </div>
              
              <div className="flex items-center justify-between p-4">
                <div>
                  <Label htmlFor="analytics" className="text-sm font-medium text-gray-700">
                    {locale === 'zh-CN' ? '使用分析' : 'Usage Analytics'}
                  </Label>
                  <p className="text-xs text-gray-500">
                    {locale === 'zh-CN' ? '共享匿名使用数据' : 'Share anonymous usage data'}
                  </p>
                </div>
                <div className="flex items-center">
                  <div 
                    className={`flex items-center justify-center w-16 h-8 rounded-md font-medium text-sm ${
                      analyticsEnabled 
                        ? 'bg-indigo-600 text-white' 
                        : 'bg-gray-200 text-gray-500'
                    }`}
                    onClick={() => setAnalyticsEnabled(!analyticsEnabled)}
                    style={{ cursor: 'pointer' }}
                  >
                    {locale === 'zh-CN' 
                      ? (analyticsEnabled ? '开启' : '关闭') 
                      : (analyticsEnabled ? 'ON' : 'OFF')
                    }
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
} 