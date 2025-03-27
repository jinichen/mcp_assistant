"use client"

import React, { useState, useRef, useEffect } from "react";
import { Sparkles, Send, ImagePlus, Loader2, X } from "lucide-react";
import { toast } from "sonner";
import MainLayout from "@/components/MainLayout";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ChatMessage } from "@/components/chat-message";
import dynamic from 'next/dynamic';
import { streamChatCompletion, getAvailableModels } from "@/lib/api";
import { useParams } from 'next/navigation';

// Import the ImageUpload component
const ImageUpload = dynamic(() => import('@/components/image-upload').then(mod => mod.ImageUpload), {
  ssr: false,
  loading: () => <div style={{ height: '40px', width: '100%', backgroundColor: '#f3f4f6', borderRadius: '8px' }}></div>
});

// Function to ensure content has proper spacing between words
const ensureProperSpacing = (text: string) => {
  if (!text) return '';

  // Log the original text for debugging
  console.log('Before processing:', JSON.stringify(text));
  
  // No active text processing, preserve original format
  // If specific issues are found later, targeted fixes can be added here
  const processed = text;
  
  // Log the result for comparison
  console.log('After processing:', JSON.stringify(processed));
  
  return processed;
};

export default function ChatPage() {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const [pendingImages, setPendingImages] = useState<any[]>([]);
  const [showImageUpload, setShowImageUpload] = useState(false);
  const [selectedModel, setSelectedModel] = useState<string>("gpt-4");
  const [isLoadingModels, setIsLoadingModels] = useState(true);
  const [availableModels, setAvailableModels] = useState<any[]>([]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // In client components, useParams() is the safe way to access route parameters
  const params = useParams();
  const locale = Array.isArray(params.locale) ? params.locale[0] : params.locale as string;

  useEffect(() => {
    const fetchModels = async () => {
      try {
        setIsLoadingModels(true);
        const data = await getAvailableModels();
        setAvailableModels(data.models || []);
        
        if (data.default && !selectedModel) {
          setSelectedModel(data.default);
        } else if (data.models && data.models.length > 0) {
          setSelectedModel(data.models[0].id);
        }
      } catch (err) {
        console.error('Error loading models:', err);
        toast.error(locale === 'zh-CN' ? '加载可用模型失败' : 'Failed to load available models');
      } finally {
        setIsLoadingModels(false);
      }
    };
    
    fetchModels();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoading || (!input.trim() && pendingImages.length === 0)) return;
    
    const userMessage = {
      role: 'user',
      content: pendingImages.length > 0 
        ? [
            ...(input.trim() ? [{ type: 'text', text: input }] : []),
            ...pendingImages.map(img => ({ type: 'image_url', image_url: img.image_url }))
          ]
        : input.trim()
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    setInput('');
    setPendingImages([]);
    setShowImageUpload(false);
    
    setIsLoading(true);
    
    try {
      const aiMessage = { role: 'assistant', content: '', streaming: true };
      setMessages(prev => [...prev, aiMessage]);
      
      const response = await streamChatCompletion(
        messages.concat(userMessage),
        selectedModel
      );
      
      setMessages(prev => [
        ...prev.slice(0, -1),
        { 
          role: 'assistant', 
          content: response.content,
          tool_calls: response.tool_calls
        }
      ]);
      
      if (response.tool_calls && response.tool_calls.length > 0) {
        for (const toolCall of response.tool_calls) {
          handleToolCall(toolCall);
        }
      }
    } catch (err: any) {
      console.error('Error getting completion:', err);
      setMessages(prev => prev.filter(m => !m.streaming));
      
      // Display formatted error message
      const errorMessage = {
        role: 'assistant',
        content: formatErrorMessage(err, locale)
      };
      setMessages(prev => [...prev, errorMessage]);
      
      toast.error(locale === 'zh-CN' ? '获取AI响应失败' : 'Failed to get response from AI');
    } finally {
      setIsLoading(false);
    }
  };

  // Format error messages to be more user-friendly
  const formatErrorMessage = (error: any, locale: string) => {
    let errorMsg = '';
    
    if (locale === 'zh-CN') {
      errorMsg = '抱歉，我在处理您的请求时遇到了问题。\n\n';
      
      if (error.message?.includes('Invalid argument') || error.message?.includes('unexpectedmodel')) {
        errorMsg += '当前模型配置有误。请尝试在下方选择其他模型。';
      } else if (error.message?.includes('timeout')) {
        errorMsg += '服务器响应超时，请稍后再试。';
      } else {
        errorMsg += '这可能是临时性问题，请稍后再试。或者尝试重新加载页面。';
      }
    } else {
      errorMsg = 'I apologize, but I encountered an issue processing your request.\n\n';
      
      if (error.message?.includes('Invalid argument') || error.message?.includes('unexpectedmodel')) {
        errorMsg += 'There appears to be an issue with the current model configuration. Please try selecting a different model below.';
      } else if (error.message?.includes('timeout')) {
        errorMsg += 'The server request timed out. Please try again later.';
      } else {
        errorMsg += 'This might be a temporary issue. Please try again or reload the page.';
      }
    }
    
    return errorMsg;
  };

  const handleImagesUploaded = (imageData: any[]) => {
    setPendingImages(imageData);
    toast.success(locale === 'zh-CN' ? '图片已准备就绪' : 'Images ready to send');
  };
  
  const handleToolCall = async (toolCall: any) => {
    console.log('Tool call received:', toolCall);
  };

  return (
    <MainLayout activePage="chat" pageTitle={locale === 'zh-CN' ? '对话' : 'Chat'}>
      <div style={{ 
        height: "100%", 
        display: "flex", 
        flexDirection: "column", 
        backgroundColor: "#ffffff", 
        border: "1px solid rgba(229, 231, 235, 0.7)", 
        borderRadius: "12px", 
        boxShadow: "0 8px 30px rgba(0, 0, 0, 0.08)",
        overflow: "hidden"
      }}>
        {/* Chat Messages */}
        <div style={{ 
          flex: 1, 
          overflowY: "auto", 
          padding: "28px", 
          backgroundImage: "linear-gradient(to bottom right, rgba(249, 250, 251, 0.7), rgba(255, 255, 255, 0.9))",
        }}>
          {messages.length === 0 ? (
            <div style={{ 
              height: "100%", 
              display: "flex", 
              alignItems: "center", 
              justifyContent: "center", 
              flexDirection: "column", 
              gap: "24px", 
              textAlign: "center", 
              padding: "32px" 
            }}>
              <div style={{ 
                width: "90px", 
                height: "90px", 
                borderRadius: "50%", 
                background: "linear-gradient(135deg, #e0f2fe, #dbeafe)",
                display: "flex", 
                alignItems: "center", 
                justifyContent: "center", 
                marginBottom: "8px",
                boxShadow: "0 12px 24px -8px rgba(37, 99, 235, 0.15)"
              }}>
                <Sparkles style={{ color: "#3b82f6", width: "40px", height: "40px" }} />
              </div>
              <h3 style={{ 
                fontSize: "28px", 
                fontWeight: 600, 
                color: "#1e3a8a",
                letterSpacing: "-0.01em"
              }}>
                {locale === 'zh-CN' ? '开始您的对话' : 'Start Your Conversation'}
              </h3>
              <p style={{ 
                color: "#64748b", 
                maxWidth: "520px", 
                fontSize: "16px", 
                lineHeight: 1.6,
                fontWeight: "450"
              }}>
                {locale === 'zh-CN' 
                  ? '输入您的问题或上传图片，我们的AI助手将帮助您获取信息并解决问题。' 
                  : 'Enter your question or upload an image, and our AI Assistant will help you get information and solve problems.'}
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {messages.map((message, index) => (
                message.role !== 'tool' && (
                  <ChatMessage 
                    key={index} 
                    message={message} 
                    isLoading={isLoading && index === messages.length - 1}
                  />
                )
              ))}
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        {/* Chat Input */}
        <div style={{ 
          padding: "24px 28px", 
          borderTop: "1px solid rgba(229, 231, 235, 0.5)", 
          background: "linear-gradient(to bottom, #f8fafc, #f1f5f9)"
        }}>
          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
            {/* Model selector */}
            <div style={{ 
              display: "flex", 
              alignItems: "center", 
              justifyContent: "space-between", 
              gap: "16px" 
            }}>
              <h3 style={{ 
                fontSize: "14px", 
                fontWeight: 500, 
                color: "#4b5563"
              }}>
                {locale === 'zh-CN' ? 'AI 模型' : 'AI Model'}
              </h3>
              
              <Select
                value={selectedModel}
                onValueChange={setSelectedModel}
                disabled={isLoadingModels}
              >
                <SelectTrigger 
                  style={{ 
                    width: "240px", 
                    backgroundColor: "white",
                    border: "1px solid #e5e7eb",
                  }}
                >
                  <SelectValue placeholder={isLoadingModels ? (locale === 'zh-CN' ? '加载中...' : 'Loading...') : ""} />
                </SelectTrigger>
                <SelectContent>
                  {availableModels.map((model) => (
                    <SelectItem key={model.id} value={model.id}>
                      {model.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            {showImageUpload && (
              <div style={{ position: "relative" }}>
                <ImageUpload onImagesUploaded={handleImagesUploaded} />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  style={{
                    position: "absolute",
                    top: "-8px",
                    right: "-8px",
                    width: "24px",
                    height: "24px",
                    borderRadius: "50%",
                    padding: 0,
                    backgroundColor: "#f3f4f6"
                  }}
                  onClick={() => setShowImageUpload(false)}
                >
                  <X size={14} />
                </Button>
              </div>
            )}
            
            <div style={{ 
              display: "flex", 
              alignItems: "center", 
              gap: "12px",
              position: "relative"
            }}>
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={locale === 'zh-CN' ? '提问...' : 'Ask a question...'}
                style={{ 
                  flex: 1,
                  height: "50px",
                  borderRadius: "10px",
                  border: "1px solid #e5e7eb",
                  padding: "0 16px",
                  fontSize: "16px",
                  backgroundColor: "white",
                  boxShadow: "0 2px 4px rgba(0, 0, 0, 0.03)",
                  outline: "none",
                }}
                disabled={isLoading}
              />
              
              {!showImageUpload && (
                <Button
                  type="button"
                  variant="ghost"
                  style={{
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    width: "50px",
                    height: "50px",
                    borderRadius: "10px",
                    backgroundColor: "#f3f4f6",
                    color: "#6b7280",
                    flexShrink: 0
                  }}
                  onClick={() => setShowImageUpload(true)}
                  disabled={isLoading}
                >
                  <ImagePlus size={20} />
                </Button>
              )}
              
              <Button 
                type="submit" 
                style={{
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  width: "50px",
                  height: "50px",
                  borderRadius: "10px",
                  backgroundColor: "#2563eb",
                  color: "white",
                  flexShrink: 0
                }}
                disabled={isLoading || (!input.trim() && pendingImages.length === 0)}
              >
                {isLoading ? (
                  <Loader2 size={20} className="animate-spin" />
                ) : (
                  <Send size={20} />
                )}
              </Button>
            </div>
            
            {pendingImages.length > 0 && (
              <div style={{ fontSize: "14px", color: "#4b5563" }}>
                {locale === 'zh-CN' 
                  ? `${pendingImages.length} 张图片已准备就绪` 
                  : `${pendingImages.length} image${pendingImages.length > 1 ? 's' : ''} ready to send`}
              </div>
            )}
          </form>
        </div>
      </div>
    </MainLayout>
  );
} 