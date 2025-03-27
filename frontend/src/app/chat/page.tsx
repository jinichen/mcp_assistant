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
        toast.error('Failed to load available models');
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
          content: ensureProperSpacing(response.content),
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
      
      toast.error('Failed to get response from AI');
    } finally {
      setIsLoading(false);
    }
  };

  const handleImagesUploaded = (imageData: any[]) => {
    setPendingImages(imageData);
    toast.success('Images ready to send');
  };
  
  const handleToolCall = async (toolCall: any) => {
    console.log('Tool call received:', toolCall);
  };

  return (
    <MainLayout activePage="chat" pageTitle="AI Chat">
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
                Start Your Conversation
              </h3>
              <p style={{ 
                color: "#64748b", 
                maxWidth: "520px", 
                fontSize: "16px", 
                lineHeight: 1.6,
                fontWeight: "450"
              }}>
                Enter your question or upload an image, and our AI Assistant will help you get information and solve problems.
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
                color: "#475569",
                letterSpacing: "0.02em"
              }}>
                AI Model
              </h3>
              <Select 
                value={selectedModel} 
                onValueChange={setSelectedModel}
                disabled={isLoadingModels || isLoading}
              >
                <SelectTrigger style={{ 
                  width: "250px", 
                  backgroundColor: "white", 
                  border: "1px solid rgba(203, 213, 225, 0.8)", 
                  transition: "all 0.2s",
                  borderRadius: "8px",
                  boxShadow: "0 2px 5px rgba(0, 0, 0, 0.03)"
                }}>
                  <SelectValue placeholder="Select model" />
                </SelectTrigger>
                <SelectContent style={{ 
                  backgroundColor: "white", 
                  border: "1px solid rgba(203, 213, 225, 0.8)",
                  boxShadow: "0 8px 30px rgba(0, 0, 0, 0.1)"
                }}>
                  {availableModels.map((model) => (
                    <SelectItem key={model.id} value={model.id}>
                      {model.name || model.id}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div style={{ position: "relative" }}>
              <Input
                placeholder="Ask a question..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={isLoading}
                style={{ 
                  paddingRight: "96px", 
                  height: "60px", 
                  fontSize: "16px", 
                  borderRadius: "12px", 
                  paddingLeft: "22px", 
                  backgroundColor: "white", 
                  border: "1px solid rgba(203, 213, 225, 0.6)", 
                  color: "#334155", 
                  transition: "all 0.2s",
                  boxShadow: "0 4px 10px rgba(0, 0, 0, 0.03)"
                }}
              />
              <div style={{ 
                position: "absolute", 
                right: "10px", 
                top: "50%", 
                transform: "translateY(-50%)", 
                display: "flex", 
                alignItems: "center", 
                gap: "8px" 
              }}>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => setShowImageUpload(!showImageUpload)}
                  disabled={isLoading}
                  style={{ 
                    height: "42px", 
                    width: "42px", 
                    borderRadius: "50%", 
                    backgroundColor: showImageUpload ? "rgba(59, 130, 246, 0.1)" : "transparent", 
                    color: "#3b82f6", 
                    transition: "all 0.2s" 
                  }}
                >
                  <ImagePlus size={20} />
                </Button>
                <Button 
                  type="submit" 
                  size="icon" 
                  disabled={isLoading || (!input.trim() && pendingImages.length === 0)} 
                  style={{ 
                    height: "42px", 
                    width: "42px", 
                    borderRadius: "50%", 
                    background: "linear-gradient(135deg, #3b82f6, #2563eb)", 
                    color: "white", 
                    transition: "all 0.2s", 
                    boxShadow: "0 4px 10px rgba(37, 99, 235, 0.3)" 
                  }}
                >
                  {isLoading ? 
                    <Loader2 style={{ height: "20px", width: "20px", animation: "spin 1s linear infinite" }} /> : 
                    <Send style={{ height: "18px", width: "18px" }} />
                  }
                </Button>
              </div>
            </div>
            
            {/* Image upload component */}
            {showImageUpload && (
              <div style={{ 
                marginTop: "16px", 
                padding: "20px", 
                backgroundColor: "white", 
                borderRadius: "12px", 
                border: "1px solid rgba(203, 213, 225, 0.5)", 
                boxShadow: "0 4px 15px rgba(0, 0, 0, 0.05)" 
              }}>
                <ImageUpload 
                  onImagesUploaded={handleImagesUploaded}
                />
              </div>
            )}
            
            {/* Preview of pending images */}
            {pendingImages.length > 0 && (
              <div style={{ 
                display: "flex", 
                flexWrap: "wrap", 
                gap: "12px", 
                marginTop: "16px" 
              }}>
                {pendingImages.map((img, idx) => (
                  <div key={idx} style={{ 
                    position: "relative", 
                    height: "80px", 
                    width: "80px", 
                    overflow: "hidden", 
                    borderRadius: "10px", 
                    border: "1px solid rgba(203, 213, 225, 0.5)", 
                    boxShadow: "0 4px 10px rgba(0, 0, 0, 0.05)", 
                    transition: "transform 0.2s",
                    transform: "scale(1)"
                  }} 
                  className="hover-lift"
                  >
                    <img 
                      src={img.image_url} 
                      alt={`Upload ${idx}`}
                      style={{ height: "100%", width: "100%", objectFit: "cover" }} 
                    />
                    <button
                      type="button"
                      onClick={() => setPendingImages(prev => prev.filter((_, i) => i !== idx))}
                      style={{ 
                        position: "absolute", 
                        top: "4px", 
                        right: "4px", 
                        background: "linear-gradient(135deg, #ef4444, #dc2626)", 
                        color: "white", 
                        borderRadius: "50%", 
                        padding: "6px", 
                        boxShadow: "0 2px 5px rgba(220, 38, 38, 0.3)", 
                        transition: "all 0.2s" 
                      }}
                    >
                      <X size={12} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </form>
        </div>
      </div>
    </MainLayout>
  );
} 