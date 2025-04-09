"use client";

import React, { useState, useRef, useEffect } from "react";
import MainLayout from "@/components/layout/main-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Send } from "lucide-react";
import { User } from "lucide-react";
import { Bot } from "lucide-react";
import { Sparkles } from "lucide-react";
import { Calculator } from "lucide-react";
import { Cloud } from "lucide-react";
import { Upload } from "lucide-react";
import { useAuth } from "../../../context/auth-context";
import { useRouter, useParams } from "next/navigation";
import { getDictionary } from "@/lib/dictionary";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  IconButton,
  ModeToggle,
  LanguageToggle,
  Label,
  LoadingDots,
  ImagePlus,
  MessageSquare,
  Home,
  User2,
} from "@/components/ui/icons";

// Message types for MCP
interface Message {
  role: string;
  content: string;
  tool_used?: string;
  is_tool_response?: boolean;
}

// API configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';
const MCP_API_URL = 'http://localhost:8001/api/v1/mcp';

export default function ChatPage() {
  const [inputValue, setInputValue] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [conversationId, setConversationId] = useState<string>("");
  const [isLoginModalOpen, setIsLoginModalOpen] = useState<boolean>(false);
  const [username, setUsername] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [email, setEmail] = useState<string>("");
  const [loginError, setLoginError] = useState<string>("");
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [registerSuccess, setRegisterSuccess] = useState(false);
  const [selectedTool, setSelectedTool] = useState("");
  const [availableTools, setAvailableTools] = useState<
    { id: string; name: string; description: string }[]
  >([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const params = useParams();
  const lang = (params?.lang as string) || "en";
  const dictionary = getDictionary(lang);

  const { token, isAuthenticated, login, logout } = useAuth();
  const router = useRouter();
  
  // Extract required dictionaries from dictionary
  const t = dictionary.chat;

  // Ensure authentication status is checked on component mount
  useEffect(() => {
    // Force check authentication status
    console.log('Authentication status check:', isAuthenticated);
    setIsLoginModalOpen(!isAuthenticated);
  }, []);

  // Improved login check logic to ensure login modal is always shown when not authenticated
  useEffect(() => {
    // Directly determine whether to show login modal based on authentication status
    if (!isAuthenticated) {
      console.log('User not authenticated, showing login modal');
      setIsLoginModalOpen(true);
    } else {
      console.log('User authenticated, hiding login modal');
      setIsLoginModalOpen(false);
    }
  }, [isAuthenticated]);

  // Auto-scroll to the latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Reset state when switching to register mode
  const toggleRegisterMode = () => {
    setIsRegisterMode(!isRegisterMode);
    setUsername("");
    setPassword("");
    setEmail("");
    setLoginError("");
    setRegisterSuccess(false);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError("");
    
    try {
      // Use OAuth2 standard form format for request
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      
      // Call backend login API
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('Login failed');
      }
      
      const data = await response.json();
      
      // Call login method with token and user data
      login(data.access_token, { username: username });
      setIsLoginModalOpen(false);
    } catch (error) {
      console.error('Login error:', error);
      setLoginError(t.login.error);
    }
  };

  // Register new user
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError("");
    setRegisterSuccess(false);
    
    try {
      console.log("Registration data:", { username, email, password });
      
      // Call backend registration API
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: username,
          email: email,
          password: password
        }),
      });
      
      console.log("Registration response status:", response.status);
      
      const responseData = await response.json();
      console.log("Registration response data:", responseData);
      
      if (!response.ok) {
        const errorMessage = responseData.detail || 'Registration failed';
        console.error("Registration error details:", errorMessage);
        throw new Error(errorMessage);
      }
      
      // Registration successful
      setRegisterSuccess(true);
      
      // Switch back to login mode after 3 seconds
      setTimeout(() => {
        setIsRegisterMode(false);
      }, 3000);
      
    } catch (error) {
      console.error('Register error:', error);
      if (error instanceof Error) {
        setLoginError(error.message);
      } else {
        setLoginError(t.register.error);
      }
    }
  };

  // Create a new conversation
  const createConversation = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/conversations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          title: "New Conversation",
          conversation_type: "text",
          // Don't specify provider, use backend default
          model: undefined
        })
      });

      if (!response.ok) throw new Error('Failed to create conversation');
      
      const data = await response.json();
      console.log('Created conversation:', data);
      return data.id;
    } catch (error) {
      console.error('Error creating conversation:', error);
      return null;
    }
  };

  // Get available tools
  useEffect(() => {
    const fetchTools = async () => {
      try {
        const response = await fetch(`${MCP_API_URL}/tools`);
        const data = await response.json();
        if (data.tools) {
          setAvailableTools([
            { id: "", name: t.tools.default || "Default AI", description: "" },
            ...data.tools.map((tool: any) => ({
              id: tool.id,
              name: tool.name,
              description: tool.description
            }))
          ]);
        }
      } catch (error) {
        console.error("Error fetching tools:", error);
        // If tool fetch fails, at least set default AI option
        setAvailableTools([
          { id: "", name: t.tools.default || "Default AI", description: "" }
        ]);
      }
    };

    fetchTools();
  }, [t]);

  // Modify handleSubmit function to use unified MCP API endpoint
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputValue.trim()) return;
    
    // Add user message to chat
    const userMessage = { role: 'user', content: inputValue };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInputValue("");
    
    // Show loading state
    setIsLoading(true);
    
    try {
      // Use MCP API endpoint to let model automatically select tool
      const apiUrl = `${MCP_API_URL}/complete`;
      
      // Build request body
      const requestBody = {
        messages: [{ role: 'user', content: inputValue }],
        // Don't specify tool, let model choose automatically
      };
      
      console.log("Sending request to:", apiUrl);
      console.log("Request body:", requestBody);
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestBody)
      });
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Process response
      const assistantMessage = {
        role: 'assistant',
        content: data.message,
        tool_used: data.tool_info?.tool_id,
        is_tool_response: !!data.tool_info
      };
      
      setMessages([...updatedMessages, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      // Add error message
      setMessages([
        ...updatedMessages,
        { 
          role: 'assistant', 
          content: t.chat.errorMessage || "Sorry, there was an error processing your request." 
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const getMessageIcon = (message: Message) => {
    if (message.role === "user") {
      return <User className="h-5 w-5 text-primary-foreground" />;
    }
    
    return <Bot className="h-5 w-5 text-primary" />;
  };

  if (isLoginModalOpen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        {/* Fullscreen frosted glass overlay */}
        <div className="fixed inset-0 bg-background/90 backdrop-blur-2xl"></div>
        
        <div className="relative z-50 w-full max-w-md animate-in fade-in-50 zoom-in-95">
          <div className="bg-background p-8 rounded-2xl shadow-xl border border-primary/10">
            <div className="mb-6 flex justify-center">
              <div className="w-16 h-16 rounded-full bg-gradient-to-r from-primary to-indigo-500 flex items-center justify-center shadow-lg">
                <Sparkles className="h-8 w-8 text-white" />
              </div>
            </div>
            
            <h2 className="text-2xl font-bold mb-3 text-center bg-gradient-to-r from-primary to-indigo-500 text-transparent bg-clip-text">
              {isRegisterMode ? t.register.title : t.login.title}
            </h2>
            <p className="text-center mb-8 text-muted-foreground">
              {isRegisterMode ? t.register.description || "Please register to use the AI assistant" : t.login.description || "Please login to continue using the AI assistant"}
            </p>
            
            {/* Success message */}
            {registerSuccess && (
              <div className="mb-6 p-4 bg-green-100/20 text-green-600 rounded-lg border border-green-600/20 flex items-center shadow-sm">
                <div className="mr-3 flex-shrink-0">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                {t.register.success}
              </div>
            )}
            
            {/* Error message */}
            {loginError && (
              <div className="mb-6 p-4 bg-destructive/10 text-destructive rounded-lg border border-destructive/20 flex items-center shadow-sm">
                <div className="mr-3 flex-shrink-0">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                {loginError}
              </div>
            )}
            
            {isRegisterMode ? (
              // Registration form
              <form onSubmit={handleRegister} className="space-y-5">
                <div className="space-y-2">
                  <label htmlFor="username" className="block text-sm font-medium mb-1">
                    {t.register.username}
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <User2 className="h-5 w-5 text-primary/60" />
                    </div>
                    <Input
                      id="username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder={t.register.usernamePlaceholder}
                      className="pl-10 bg-background border-primary/20 focus:border-primary"
                      required
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <label htmlFor="email" className="block text-sm font-medium mb-1">
                    {t.register.email}
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary/60" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                        <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
                      </svg>
                    </div>
                    <Input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder={t.register.emailPlaceholder}
                      className="pl-10 bg-background border-primary/20 focus:border-primary"
                      required
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <label htmlFor="password" className="block text-sm font-medium mb-1">
                    {t.register.password}
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary/60" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <Input
                      id="password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder={t.register.passwordPlaceholder}
                      className="pl-10 bg-background border-primary/20 focus:border-primary"
                      minLength={8}
                      required
                    />
                  </div>
                </div>
                
                <Button 
                  type="submit" 
                  className="w-full h-11 bg-gradient-to-r from-primary to-indigo-500 hover:opacity-90 text-white font-medium transition-all shadow-md hover:shadow-lg shadow-primary/20 hover:shadow-primary/30"
                >
                  {t.register.button}
                </Button>
                
                <div className="mt-6 text-center text-sm">
                  <span className="text-muted-foreground">{t.login.haveAccount}</span>{" "}
                  <button 
                    type="button" 
                    onClick={toggleRegisterMode}
                    className="text-primary hover:text-primary/80 font-medium transition-colors"
                  >
                    {t.login.loginLink}
                  </button>
                </div>
              </form>
            ) : (
              // Login form
              <form onSubmit={handleLogin} className="space-y-5">
                <div className="space-y-2">
                  <label htmlFor="username" className="block text-sm font-medium mb-1">
                    {t.login.username}
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <User2 className="h-5 w-5 text-primary/60" />
                    </div>
                    <Input
                      id="username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder={t.login.usernamePlaceholder}
                      className="pl-10 bg-background border-primary/20 focus:border-primary"
                      required
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <label htmlFor="password" className="block text-sm font-medium mb-1">
                    {t.login.password}
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary/60" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <Input
                      id="password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder={t.login.passwordPlaceholder}
                      className="pl-10 bg-background border-primary/20 focus:border-primary"
                      required
                    />
                  </div>
                </div>
                
                <Button 
                  type="submit" 
                  className="w-full h-11 bg-gradient-to-r from-primary to-indigo-500 hover:opacity-90 text-white font-medium transition-all shadow-md hover:shadow-lg shadow-primary/20 hover:shadow-primary/30"
                >
                  {t.login.button}
                </Button>
                
                <div className="mt-6 text-center text-sm">
                  <span className="text-muted-foreground">{t.login.noAccount}</span>{" "}
                  <button 
                    type="button" 
                    onClick={toggleRegisterMode}
                    className="text-primary hover:text-primary/80 font-medium transition-colors"
                  >
                    {t.login.registerLink}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <MainLayout dictionary={dictionary}>
      <div className="container mx-auto px-4 py-6">
        <div className="rounded-lg border border-primary/10 shadow-lg bg-gradient-to-b from-background to-muted/30 backdrop-blur-sm transition-all duration-300 hover:shadow-primary/5">
          {/* Chat messages area */}
          <div className="h-[70vh] overflow-y-auto p-4 scrollbar-thin scrollbar-thumb-primary/10 scrollbar-track-transparent">
            {/* Welcome message */}
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="mb-6 rounded-full bg-primary/10 p-4 shadow-md shadow-primary/5 animate-pulse-slow">
                  <Sparkles className="h-8 w-8 text-primary" />
                </div>
                <h2 className="mb-3 text-2xl font-bold bg-gradient-to-r from-primary to-indigo-500 text-transparent bg-clip-text">{t.chat.welcome}</h2>
                <p className="mb-10 max-w-md text-muted-foreground">
                  {t.chat.description}
                </p>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3">
                  {t.welcomePrompts.map((prompt: string, i: number) => (
                    <Button
                      key={i}
                      variant="outline"
                      className="text-sm h-auto py-2 justify-start border-primary/20 hover:border-primary/30 hover:bg-primary/5 transition-all shadow-sm hover:shadow-md hover:shadow-primary/5"
                      onClick={() => {
                        setInputValue(prompt);
                        inputRef.current?.focus();
                      }}
                    >
                      <MessageSquare className="mr-2 h-4 w-4 text-primary/70" />
                      {prompt}
                    </Button>
                  ))}
                </div>
              </div>
            )}

            {/* Message list */}
            {messages.length > 0 && (
              <div className="space-y-4">
                {messages.map((message, i) => (
                  <div
                    key={i}
                    className={`flex gap-3 ${
                      message.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    {message.role !== "user" && (
                      <div className="h-8 w-8 rounded-full bg-gradient-to-br from-primary/20 to-indigo-500/20 flex items-center justify-center shadow-md">
                        <Sparkles className="h-4 w-4 text-primary" />
                      </div>
                    )}
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-3 shadow-md transition-all ${
                        message.role === "user"
                          ? "bg-gradient-to-r from-primary to-indigo-500 text-primary-foreground shadow-primary/20"
                          : message.is_tool_response
                          ? "bg-gradient-to-r from-amber-50 to-amber-100/80 text-amber-900 dark:from-amber-900/40 dark:to-amber-800/30 dark:text-amber-100 border border-amber-200/50 dark:border-amber-700/30 shadow-amber-500/10"
                          : "bg-gradient-to-r from-muted/80 to-card shadow-sm"
                      }`}
                    >
                      {message.tool_used && (
                        <div className="mb-1 flex items-center gap-1 text-xs font-medium border-b border-amber-200/50 dark:border-amber-700/50 pb-1">
                          <span className="bg-gradient-to-r from-amber-200 to-amber-300 dark:from-amber-800 dark:to-amber-700 text-amber-900 dark:text-amber-100 p-1 rounded-full flex items-center justify-center shadow-sm">
                            {message.tool_used === "math" ? (
                              <Calculator className="h-3 w-3" />
                            ) : message.tool_used === "weather" ? (
                              <Cloud className="h-3 w-3" />
                            ) : (
                              <Sparkles className="h-3 w-3" />
                            )}
                          </span>
                          <span className="font-semibold">
                            {message.tool_used.charAt(0).toUpperCase() +
                              message.tool_used.slice(1)}{" "}
                            {t.tools.result}
                          </span>
                        </div>
                      )}
                      <div className="whitespace-pre-wrap break-words">
                        {message.content}
                      </div>
                    </div>
                    {message.role === "user" && (
                      <div className="h-8 w-8 rounded-full bg-gradient-to-r from-primary to-indigo-500 flex items-center justify-center shadow-md">
                        <User2 className="h-4 w-4 text-primary-foreground" />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Loading animation */}
            {isLoading && (
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-gradient-to-br from-primary/30 to-indigo-500/30 flex items-center justify-center animate-pulse shadow-md">
                  <Sparkles className="h-4 w-4 text-primary" />
                </div>
                <div className="rounded-2xl bg-muted px-4 py-3 shadow-sm flex items-center">
                  <div className="flex space-x-2 items-center">
                    <span className="sr-only">Loading...</span>
                    <div className="h-2 w-2 bg-gradient-to-r from-primary to-indigo-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
                    <div className="h-2 w-2 bg-gradient-to-r from-indigo-500 to-primary rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
                    <div className="h-2 w-2 bg-gradient-to-r from-primary to-indigo-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
                  </div>
                </div>
              </div>
            )}

            {/* Reference point for scrolling to bottom */}
            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <div className="border-t border-primary/10 p-4 bg-background/80 backdrop-blur-sm">
            <div className="relative rounded-xl border border-primary/20 bg-card/30 focus-within:ring-2 focus-within:ring-primary/40 hover:border-primary/30 transition-all shadow-sm hover:shadow-md hover:shadow-primary/5">
              <form onSubmit={handleSubmit} className="flex items-center">
                <Textarea
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder={t.chat.inputPlaceholder}
                  className="flex-1 border-0 focus-visible:ring-0 bg-transparent min-h-[60px] max-h-[120px] resize-none py-3 px-4"
                  disabled={isLoading}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      if (inputValue.trim() && !isLoading) {
                        handleSubmit(e);
                      }
                    }
                  }}
                />
                <div className="flex items-center gap-2 pr-3">
                  <IconButton
                    variant="ghost"
                    size="sm"
                    title={t.chat.uploadImage}
                    disabled={isLoading}
                    className="text-primary/70 hover:text-primary hover:bg-primary/10"
                  >
                    <ImagePlus className="h-4 w-4" />
                    <span className="sr-only">{t.chat.uploadImage}</span>
                  </IconButton>
                  <IconButton
                    type="submit"
                    size="sm"
                    disabled={isLoading || !inputValue.trim()}
                    className="bg-gradient-to-r from-primary to-indigo-500 text-primary-foreground hover:opacity-90 shadow-sm hover:shadow-md hover:shadow-primary/10 transition-all"
                  >
                    <Send className="h-4 w-4" />
                    <span className="sr-only">{t.chat.send}</span>
                  </IconButton>
                </div>
              </form>
            </div>
            <p className="mt-3 text-xs text-center text-muted-foreground">
              {t.chat.disclaimer}
            </p>
          </div>
        </div>
      </div>
    </MainLayout>
  );
} 