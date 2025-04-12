"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import MainLayout from "@/components/layout/main-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Send, X } from "lucide-react";
import { User } from "lucide-react";
import { Bot } from "lucide-react";
import { Sparkles } from "lucide-react";
import { Calculator } from "lucide-react";
import { Cloud } from "lucide-react";
import { Upload, UploadCloud } from "lucide-react";
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
  File,
  Image,
} from "@/components/ui/icons";
import { FileUploadButton } from "@/components/upload";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from "@/lib/utils";

// Message types for MCP
interface Message {
  role: string;
  content: string;
  tool_used?: string;
  is_tool_response?: boolean;
  attachment?: {
    filename: string;
    type: string;
    url: string;
  };
  is_streaming?: boolean;
}

// API configuration
const API_BASE_URL = 'http://localhost:8000';
const API_V1_URL = `${API_BASE_URL}/api/v1`;

// Define supported tools list (used to identify tool information returned by backend)
const SUPPORTED_TOOLS = ['math', 'weather', 'search', 'code', 'agent'];

// Define common regex patterns
const langchainAIMessagePattern = /\{\s*'agent':\s*\{\s*'messages':\s*\[\s*AIMessage\(content='([^']*)'/;
const langchainContentPattern = /content=['"]([^'"]*)['"]/;

// Helper function: Process smith output format
const extractSmithOutput = (content: string): string => {
  // Check if contains smith format thinking process (various formats)
  
  // Process <think>...</think> tag format
  const thinkPattern = /<think>([\s\S]*?)<\/think>/i;
  const thinkMatch = content.match(thinkPattern);
  
  if (thinkMatch) {
    // Found thinking process, return content after thinking as conclusion
    const afterThinkContent = content.split('</think>')[1];
    if (afterThinkContent && afterThinkContent.trim()) {
      return afterThinkContent.trim();
    }
  }
  
  // Process formats without explicit tags but with clear separators
  // Check for common separator patterns like "thinking process" followed by "final answer"
  const commonSeparators = [
    /(?:\r?\n){2,}(?=As of|The current|To summarize|In conclusion|Therefore|In summary)/i
  ];
  
  for (const separator of commonSeparators) {
    const match = content.match(separator);
    if (match && match.index !== undefined) {
      // Found possible conclusion separator
      return content.substring(match.index).trim();
    }
  }

  // Check old smith output format
  const smithMatch = content.match(/smith output:([\s\S]*?)(?=$|smith output:)/i);
  if (smithMatch && smithMatch[1]) {
    // Only extract smith output part
    return smithMatch[1].trim();
  }
  
  return content;
};

// Helper function: Clean message content metadata
const cleanMessageContent = (content: string): string => {
  if (!content) return '';
  
  let cleanContent = content;
  
  // Process thinking tags, ensure complete removal of all tags and their content
  const thinkTagPattern = /<\/?think>|<\/thing>/g;
  cleanContent = cleanContent.replace(thinkTagPattern, '');
  
  // Fix incorrect newline representations
  cleanContent = cleanContent.replace(/\/n/g, '\n');
  
  // Process LangChain AIMessage format
  const aiMessageMatch = cleanContent.match(langchainAIMessagePattern);
  if (aiMessageMatch && aiMessageMatch[1]) {
    return aiMessageMatch[1];
  }
  
  // Process another common LangChain message format
  if (cleanContent.includes("'messages':") && cleanContent.includes("content=")) {
    const contentMatch = cleanContent.match(langchainContentPattern);
    if (contentMatch && contentMatch[1]) {
      return contentMatch[1];
    }
  }
  
  // Check if contains thinking process, if so extract main content
  if (cleanContent.includes('<think>') && cleanContent.includes('</think>')) {
    const thinkStartIndex = cleanContent.indexOf('<think>');
    const thinkEndIndex = cleanContent.indexOf('</think>') + '</think>'.length;
    
    if (thinkStartIndex >= 0 && thinkEndIndex > 0) {
      // Remove thinking part, keep the rest
      cleanContent = cleanContent.substring(0, thinkStartIndex) + 
                   cleanContent.substring(thinkEndIndex);
      cleanContent = cleanContent.trim();
    }
  }
  
  // Check if there's a complete JSON object, if formatted API response, needs processing
  if (cleanContent.startsWith('{') && cleanContent.endsWith('}')) {
    try {
      // Try parsing as JSON
      const jsonObj = JSON.parse(cleanContent);
      
      // If contains agent and messages fields, could be API response
      if (jsonObj.agent && jsonObj.messages) {
        // Extract last message content
        const messages = jsonObj.messages;
        if (Array.isArray(messages) && messages.length > 0) {
          const lastMessage = messages[messages.length - 1];
          if (lastMessage && lastMessage.content) {
            return lastMessage.content;
          }
        }
      }
      
      // If it's a single message object
      if (jsonObj.content) {
        return jsonObj.content;
      }
    } catch (e) {
      // JSON parsing failed, might not be a complete JSON object
      console.log("JSON parsing failed, treating as plain text", e);
    }
  }
  
  // Remove various metadata patterns but keep main content
  const patterns = [
    /response_metadata=\{.*?\}\}\}\}/g,
    /id='run-.*?'/g,
    /usage_metadata=\{.*?\}\}\}/g
  ];
  
  patterns.forEach(pattern => {
    cleanContent = cleanContent.replace(pattern, '');
  });
  
  // Special handling for agent format, extract content instead of deleting entire block
  const agentPattern = /\{'agent': \{.*?\}\}\}\}/g;
  const matches = cleanContent.match(agentPattern);
  if (matches && matches.length > 0) {
    for (const match of matches) {
      try {
        // Try to extract message content
        const contentMatch = match.match(/'content': '([^']*)'/);
        if (contentMatch && contentMatch[1]) {
          // Replace entire match with extracted content
          cleanContent = cleanContent.replace(match, contentMatch[1]);
        } else {
          // If unable to extract content, delete entire match
          cleanContent = cleanContent.replace(match, '');
        }
      } catch (e) {
        // If processing fails, delete entire match
        cleanContent = cleanContent.replace(match, '');
      }
    }
  }
  
  // Process possible metadata string
  cleanContent = cleanContent.replace(/\s*\{\s*$/, '');
  
  return cleanContent;
};

export default function ChatPage({ params }: { params: { lang: string } }) {
  // State for chat functionality
  const [inputValue, setInputValue] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  
  // State for file uploads
  const [showFileManager, setShowFileManager] = useState<boolean>(false);
  const [currentAttachment, setCurrentAttachment] = useState<{
    filename: string;
    url: string;
    type: string;
  } | null>(null);

  // State for authentication
  const [isLoginModalOpen, setIsLoginModalOpen] = useState<boolean>(false);
  const [username, setUsername] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [email, setEmail] = useState<string>("");
  const [loginError, setLoginError] = useState<string>("");
  const [isRegisterMode, setIsRegisterMode] = useState<boolean>(false);
  const [registerSuccess, setRegisterSuccess] = useState<boolean>(false);
  const [loggingIn, setLoggingIn] = useState<boolean>(false);
  const [registering, setRegistering] = useState<boolean>(false);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  
  // Setup language and dictionaries
  const lang = params?.lang || "en";
  const dictionary = getDictionary(lang);
  const chat = dictionary.chat;
  const layout = dictionary.layout;

  // Auth and router
  const { token, isAuthenticated, login, logout } = useAuth();
  const router = useRouter();

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
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // Improved auto scrolling logic
  const scrollToBottom = useCallback(() => {
    if (!messagesEndRef.current) return;
    
    messagesEndRef.current.scrollIntoView({
      behavior: 'smooth',
      block: 'end',
    });
  }, [messagesEndRef]);

  // Auto scroll to bottom when message changes
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

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
      console.log(`Attempting to login at ${API_V1_URL}/auth/login`);
      const response = await fetch(`${API_V1_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });
      
      if (!response.ok) {
        console.error(`Login failed with status: ${response.status}`);
        throw new Error('Login failed');
      }
      
      const data = await response.json();
      console.log('Login response:', data);
      
      // Call login method with token and user data
      if (data.access_token) {
        login(data.access_token, { username: username });
        setIsLoginModalOpen(false);
      } else {
        console.error('No access token in response:', data);
        throw new Error('Invalid response: Missing access token');
      }
    } catch (error) {
      console.error('Login error:', error);
      setLoginError(chat.login?.error || "Login failed. Please check your credentials.");
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
      const response = await fetch(`${API_V1_URL}/auth/register`, {
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
        setLoginError(chat.register?.error || "Registration failed. Please try again.");
      }
    }
  };

  // Create a new conversation
  const createConversation = async () => {
    try {
      const response = await fetch(`${API_V1_URL}/conversations`, {
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

  // Handle form submission for chat
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;
    
    // Call handleSendMessage with the form event
    handleSendMessage(e);
  };

  // Handle sending message to API
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue("");
    
    // Add user message to message list
    const newUserMessage: Message = {
      role: "user",
      content: userMessage,
    };

    // Add attachment if present
    if (currentAttachment) {
      newUserMessage.attachment = {
        filename: currentAttachment.filename,
        url: currentAttachment.url,
        type: currentAttachment.type,
      };
      setCurrentAttachment(null);
    }

    setMessages((prev) => [...prev, newUserMessage]);
    setIsLoading(true);
    
    // User sends message immediately scroll to bottom
    setTimeout(scrollToBottom, 50);
    
    try {
      // Check authentication
      if (!isAuthenticated || !token) {
        console.error("User not authenticated, cannot send request");
        setIsLoginModalOpen(true);
        throw new Error("Please login before sending messages");
      }
      
      // Debug: Log authentication state
      console.log("Auth state:", isAuthenticated, "Token:", token ? "exists" : "missing");
      
      // Prepare uniform request format, backend will automatically route to appropriate service
      const payload = {
        messages: [{ role: "user", content: userMessage }],
        conversation_id: conversationId || ""
      };
      
      // Add log
      console.log("Sending chat request to API");
      console.log("Payload:", JSON.stringify(payload, null, 2));

      // Make API call - Use fetch with streaming for real-time response
      const response = await fetch(`${API_V1_URL}/mcp/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      // Debug: Log response status and headers
      console.log("Response status:", response.status, response.statusText);
      console.log("Using MCP tools route for automatic tool selection");
      
      // Get and log response headers (compatible way)
      const headers: Record<string, string> = {};
      response.headers.forEach((value, name) => {
        headers[name] = value;
      });
      console.log("Response headers:", headers);
      
      // Handle authentication errors
      if (response.status === 401) {
        console.error("Authentication failed, token may have expired");
        logout(); // Force logout
        setIsLoginModalOpen(true);
        throw new Error("Authentication failed, please login again");
      }
      
      if (!response.ok) {
        // Handle error responses
        const errorText = await response.text();
        console.error("API error response:", errorText);
        throw new Error(`API error: ${response.status} - ${errorText || response.statusText}`);
      }
      
      // Create initial assistant message
      const assistantMessage: Message = {
        role: "assistant",
        content: "",
        is_streaming: true,
      };
      
      // Add placeholder message for streaming display
      setMessages((prev) => [...prev, assistantMessage]);
      
      // Create reader for response stream
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("Failed to get stream reader");
      }
      
      // Set up text decoder
      const decoder = new TextDecoder();
      let accumulatedResponse = '';
      
      // Read stream
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        // Decode data chunk
        const chunk = decoder.decode(value, { stream: true });
        console.log("Stream chunk received:", chunk);
        
        // Process SSE format data
        chunk.split('\n\n').forEach(part => {
          if (!part.trim() || !part.startsWith('data: ')) return;
          
          const data = part.replace('data: ', '').trim();
          
          // Check if this is the end marker
          if (data === '[DONE]') {
            console.log("Stream complete");
            return;
          }
          
          try {
            // Parse JSON data
            const parsed = JSON.parse(data);
            console.log("Parsed data:", parsed);
            
            // Handle content updates
            if (parsed.content) {
              accumulatedResponse += parsed.content;
              
              // Detect tool usage
              let toolUsed = null;
              if (parsed.tool_info) {
                // Tool information from MCP
                if (parsed.tool_info.tool_name) {
                  toolUsed = parsed.tool_info.tool_name;
                } else if (parsed.tool_info.agent) {
                  toolUsed = 'agent';
                }
              } else {
                // Detect tools through content
                for (const tool of SUPPORTED_TOOLS) {
                  if (accumulatedResponse.toLowerCase().includes(`using ${tool}`) || 
                      accumulatedResponse.toLowerCase().includes(`使用${tool}`)) {
                    toolUsed = tool;
                    break;
                  }
                }
              }
              
              // Update message list
              setMessages(prev => {
                const updated = [...prev];
                const lastIndex = updated.length - 1;
                
                updated[lastIndex] = {
                  role: "assistant",
                  content: accumulatedResponse,
                  is_streaming: true,
                  tool_used: toolUsed
                };
                
                return updated;
              });
              
              // Don't scroll frequently here, rely on useEffect to handle scrolling
            }
          } catch (err) {
            console.warn("Error parsing SSE data:", err);
          }
        });
      }
      
      // Stream ends complete message
      setMessages((prev) => {
        const updatedMessages = [...prev];
        const lastIndex = updatedMessages.length - 1;
        
        if (lastIndex >= 0) {
          updatedMessages[lastIndex] = {
            role: "assistant",
            content: accumulatedResponse,
            is_streaming: false,
          };
        }
        
        return updatedMessages;
      });
      
    } catch (error: any) {
      console.error("Error in chat request:", error);
      
      // Add error message
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${error.message || "Failed to get response from server. Please try again."}`,
          is_streaming: false,
        },
      ]);
    } finally {
      setIsLoading(false);
      
      // Message stream ends scroll to bottom, use requestAnimationFrame
      requestAnimationFrame(scrollToBottom);
    }
  };
  
  // Handle file upload success
  const handleFileUploadSuccess = (uploadedFile: { filename: string, url: string, type: string }) => {
    console.log("File upload successful:", uploadedFile);
    
    setCurrentAttachment({
      filename: uploadedFile.filename,
      url: uploadedFile.url,
      type: uploadedFile.type
    });
    
    // Show notification
    const fileType = uploadedFile.type === 'image' ? 'Image' : 'File';
    const notificationMessage = `${fileType} "${uploadedFile.filename}" ready to send`;
    
    // Add system message
    setMessages(prev => [
      ...prev,
      {
        role: "system",
        content: notificationMessage,
        attachment: {
          filename: uploadedFile.filename,
          url: uploadedFile.url,
          type: uploadedFile.type
        }
      }
    ]);
    
    // Close file manager after successful upload
    setShowFileManager(false);
    
    // Focus input field after upload
    inputRef.current?.focus();
    
    // Scroll to bottom
    setTimeout(() => {
      scrollToBottom();
    }, 100);
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
              {isRegisterMode ? (chat.register?.title || "Register") : (chat.login?.title || "Login")}
            </h2>
            <p className="text-center mb-8 text-muted-foreground">
              {isRegisterMode ? 
                (chat.register?.description || "Please register to use the AI assistant") : 
                (chat.login?.description || "Please login to continue using the AI assistant")}
            </p>
            
            {/* Success message */}
            {registerSuccess && (
              <div className="mb-6 p-4 bg-green-100/20 text-green-600 rounded-lg border border-green-600/20 flex items-center shadow-sm">
                <div className="mr-3 flex-shrink-0">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                {chat.register?.success || "Registration successful! You can now login."}
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
                    {chat.register?.username || "Username"}
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <User2 className="h-5 w-5 text-primary/60" />
                    </div>
                    <Input
                      id="username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder={chat.register?.usernamePlaceholder || "Choose a username"}
                      className="pl-10 bg-background border-primary/20 focus:border-primary"
                      required
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <label htmlFor="email" className="block text-sm font-medium mb-1">
                    {chat.register?.email || "Email"}
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
                      placeholder={chat.register?.emailPlaceholder || "Enter your email"}
                      className="pl-10 bg-background border-primary/20 focus:border-primary"
                      required
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <label htmlFor="password" className="block text-sm font-medium mb-1">
                    {chat.register?.password || "Password"}
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
                      placeholder={chat.register?.passwordPlaceholder || "Create a password (min 8 characters)"}
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
                  {chat.register?.button || "Register"}
                </Button>
                
                <div className="mt-6 text-center text-sm">
                  <span className="text-muted-foreground">{chat.login?.haveAccount || "Already have an account?"}</span>{" "}
                  <button 
                    type="button" 
                    onClick={toggleRegisterMode}
                    className="text-primary hover:text-primary/80 font-medium transition-colors"
                  >
                    {chat.login?.loginLink || "Login here"}
                  </button>
                </div>
              </form>
            ) : (
              // Login form
              <form onSubmit={handleLogin} className="space-y-5">
                <div className="space-y-2">
                  <label htmlFor="username" className="block text-sm font-medium mb-1">
                    {chat.login?.username || "Username"}
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <User2 className="h-5 w-5 text-primary/60" />
                    </div>
                    <Input
                      id="username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder={chat.login?.usernamePlaceholder || "Enter your username"}
                      className="pl-10 bg-background border-primary/20 focus:border-primary"
                      required
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <label htmlFor="password" className="block text-sm font-medium mb-1">
                    {chat.login?.password || "Password"}
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
                      placeholder={chat.login?.passwordPlaceholder || "Enter your password"}
                      className="pl-10 bg-background border-primary/20 focus:border-primary"
                      required
                    />
                  </div>
                </div>
                
                <Button 
                  type="submit" 
                  className="w-full h-11 bg-gradient-to-r from-primary to-indigo-500 hover:opacity-90 text-white font-medium transition-all shadow-md hover:shadow-lg shadow-primary/20 hover:shadow-primary/30"
                >
                  {chat.login?.button || "Login"}
                </Button>
                
                <div className="mt-6 text-center text-sm">
                  <span className="text-muted-foreground">{chat.login?.noAccount || "Don't have an account?"}</span>{" "}
                  <button 
                    type="button" 
                    onClick={toggleRegisterMode}
                    className="text-primary hover:text-primary/80 font-medium transition-colors"
                  >
                    {chat.login?.registerLink || "Register here"}
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
      <div className="h-full flex flex-col overflow-hidden relative">
        <div className="flex-1 flex flex-col overflow-hidden rounded-lg border border-primary/10 shadow-lg bg-gradient-to-b from-background to-muted/30 backdrop-blur-sm transition-all duration-300 hover:shadow-primary/5">
          {/* Chat messages area - Use fixed height and bottom padding to ensure space stability */}
          <div 
            className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-primary/10 scrollbar-track-transparent chat-messages-container"
            style={{ height: "calc(100vh - 180px)", paddingBottom: "120px" }}
            ref={scrollContainerRef}
          >
            <div className="p-4">
              {/* Welcome message */}
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <div className="mb-6 rounded-full bg-primary/10 p-4 shadow-md shadow-primary/5 animate-pulse-slow">
                    <Sparkles className="h-8 w-8 text-primary" />
                  </div>
                  <h2 className="mb-3 text-2xl font-bold bg-gradient-to-r from-primary to-indigo-500 text-transparent bg-clip-text">
                    {(chat.welcome?.title) || chat.chat?.welcome || "Welcome to AI Assistant"}
                  </h2>
                  <p className="mb-10 max-w-md text-muted-foreground">
                    {(chat.welcome?.description) || chat.chat?.description || "Your AI assistant is ready to help."}
                  </p>
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3">
                    {(chat.welcome?.prompts || chat.welcomePrompts || []).map((prompt: string, i: number) => (
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
                              {chat.tools?.result || "Tool result"}
                            </span>
                          </div>
                        )}
                        <div className="whitespace-pre-wrap break-words text-base leading-relaxed max-w-full overflow-x-auto">
                          {message.content && (() => {
                            const contentStr = message.content.toString();
                            
                            // Process escape characters
                            const processedContent = contentStr
                              .replace(/\\n\\n/g, '\n\n')  // Replace \n\n
                              .replace(/\\n/g, '\n');      // Replace \n
                            
                            // Check if content includes thinking process
                            const hasThinkingContent = processedContent.includes('<think>') && processedContent.includes('</think>');
                            
                            if (hasThinkingContent) {
                              // Extract thinking content and actual content
                              const thinkPattern = /<think>([\s\S]*?)<\/think>/i;
                              const thinkMatch = processedContent.match(thinkPattern);
                              
                              if (thinkMatch && thinkMatch[1]) {
                                const thinkingContent = thinkMatch[1].trim();
                                const actualContent = processedContent.replace(thinkPattern, '').trim();
                                
                                return (
                                  <>
                                    {/* Thinking process part - Light display */}
                                    <div className="thinking-content text-muted-foreground/60 bg-muted/30 p-2 rounded mb-3 border border-muted/30 text-sm">
                                      <div className="font-medium text-xs mb-1 text-primary/50">
                                        {chat.chat?.thinking_process || "Thinking process:"}
                                      </div>
                                      <ReactMarkdown 
                                        remarkPlugins={[remarkGfm]}
                                        components={{
                                          // Custom link, open in new tab
                                          a: ({node, ...props}) => <a {...props} target="_blank" rel="noopener noreferrer" className="text-primary/60 hover:underline" />,
                                          // Ensure code block formatting is correct
                                          pre: ({node, ...props}) => <pre {...props} className="bg-muted/80 p-4 rounded-lg my-3 overflow-x-auto shadow-sm border border-muted" />,
                                          code: ({node, inline, className, children, ...props}: any) => {
                                            const isInline = Boolean(inline);
                                            const match = /language-(\w+)/.exec(className || '');
                                            return isInline 
                                              ? <code className={cn("bg-muted px-1.5 py-0.5 rounded text-sm font-mono", className)} {...props}>{children}</code>
                                              : <code className={cn(
                                                  "block overflow-x-auto max-w-full p-4 font-mono text-sm leading-relaxed",
                                                  match ? `language-${match[1]}` : '',
                                                  className
                                                )} {...props}>{children}</code>
                                          },
                                          // Custom list styles
                                          ul: ({node, ...props}) => <ul {...props} className="list-disc ml-6 my-2" />,
                                          ol: ({node, ...props}) => <ol {...props} className="list-decimal ml-6 my-2" />,
                                        }}
                                      >
                                        {thinkingContent}
                                      </ReactMarkdown>
                                    </div>
                                    
                                    {/* Actual content part - Normal display */}
                                    {actualContent && (
                                      <div className="actual-content">
                                        <ReactMarkdown 
                                          remarkPlugins={[remarkGfm]}
                                          components={{
                                            // Custom link, open in new tab
                                            a: ({node, ...props}) => <a {...props} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline" />,
                                            // Ensure code block formatting is correct
                                            pre: ({node, ...props}) => <pre {...props} className="bg-muted/80 p-4 rounded-lg my-3 overflow-x-auto shadow-sm border border-muted" />,
                                            code: ({node, inline, className, children, ...props}: any) => {
                                              const isInline = Boolean(inline);
                                              const match = /language-(\w+)/.exec(className || '');
                                              return isInline 
                                                ? <code className={cn("bg-muted px-1.5 py-0.5 rounded text-sm font-mono", className)} {...props}>{children}</code>
                                                : <code className={cn(
                                                    "block overflow-x-auto max-w-full p-4 font-mono text-sm leading-relaxed",
                                                    match ? `language-${match[1]}` : '',
                                                    className
                                                  )} {...props}>{children}</code>
                                            },
                                            // Custom list styles
                                            ul: ({node, ...props}) => <ul {...props} className="list-disc ml-6 my-2" />,
                                            ol: ({node, ...props}) => <ol {...props} className="list-decimal ml-6 my-2" />,
                                            // Custom title styles
                                            h1: ({node, ...props}) => <h1 {...props} className="text-xl font-bold my-2" />,
                                            h2: ({node, ...props}) => <h2 {...props} className="text-lg font-bold my-2" />,
                                            h3: ({node, ...props}) => <h3 {...props} className="text-md font-bold my-2" />,
                                            // Custom paragraph styles
                                            p: ({node, ...props}) => <p {...props} className="my-2 break-words" />,
                                          }}
                                        >
                                          {actualContent}
                                        </ReactMarkdown>
                                      </div>
                                    )}
                                  </>
                                );
                              }
                            }
                            
                            // Default rendering (no thinking process)
                            return (
                              <ReactMarkdown 
                                remarkPlugins={[remarkGfm]}
                                components={{
                                  // Custom link, open in new tab
                                  a: ({node, ...props}) => <a {...props} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline" />,
                                  // Ensure code block formatting is correct
                                  pre: ({node, ...props}) => <pre {...props} className="bg-muted/80 p-4 rounded-lg my-3 overflow-x-auto shadow-sm border border-muted" />,
                                  code: ({node, inline, className, children, ...props}: any) => {
                                    const isInline = Boolean(inline);
                                    const match = /language-(\w+)/.exec(className || '');
                                    return isInline 
                                      ? <code className={cn("bg-muted px-1.5 py-0.5 rounded text-sm font-mono", className)} {...props}>{children}</code>
                                      : <code className={cn(
                                          "block overflow-x-auto max-w-full p-4 font-mono text-sm leading-relaxed",
                                          match ? `language-${match[1]}` : '',
                                          className
                                        )} {...props}>{children}</code>
                                  },
                                  // Custom list styles
                                  ul: ({node, ...props}) => <ul {...props} className="list-disc ml-6 my-2" />,
                                  ol: ({node, ...props}) => <ol {...props} className="list-decimal ml-6 my-2" />,
                                  // Custom title styles
                                  h1: ({node, ...props}) => <h1 {...props} className="text-xl font-bold my-2" />,
                                  h2: ({node, ...props}) => <h2 {...props} className="text-lg font-bold my-2" />,
                                  h3: ({node, ...props}) => <h3 {...props} className="text-md font-bold my-2" />,
                                  // Custom paragraph styles
                                  p: ({node, ...props}) => <p {...props} className="my-2 break-words" />,
                                }}
                              >
                                {processedContent}
                              </ReactMarkdown>
                            );
                          })()}
                          {/* Streaming output effect - Add blinking cursor */}
                          {message.is_streaming && (
                            <span className="inline-block ml-1 h-4 w-1 bg-primary/70 animate-pulse-fast"></span>
                          )}
                        </div>
                        {message.attachment && (
                          <div className="mt-2 p-2 bg-background/20 rounded border">
                            <div className="flex items-center space-x-2">
                              {message.attachment.type === 'image' ? (
                                <Image size={16} />
                              ) : (
                                <File size={16} />
                              )}
                              <span className="text-sm">{message.attachment.filename}</span>
                            </div>
                          </div>
                        )}
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
              <div ref={messagesEndRef} style={{ height: "1px", margin: "0" }} />
            </div>
          </div>

          {/* Input area - Use fixed positioning to be at the bottom */}
          <div 
            className="border-t border-primary/10 bg-background/95 backdrop-blur-lg shadow-lg z-20 fixed bottom-0 left-0 right-0 mx-auto"
            style={{ 
              maxWidth: "calc(100% - 2rem)", 
              width: "100%", 
              marginLeft: "auto", 
              marginRight: "auto",
              borderRadius: "0 0 0.5rem 0.5rem"
            }}
          >
            <div className="p-4">
              <div className="relative rounded-xl border border-primary/20 bg-card/30 focus-within:ring-2 focus-within:ring-primary/40 hover:border-primary/30 transition-all shadow-sm hover:shadow-md hover:shadow-primary/5">
                {/* File upload panel */}
                {showFileManager && (
                  <div className="absolute bottom-full left-0 right-0 mb-2 p-3 border rounded-lg bg-background shadow-md z-10">
                    <div className="mb-2 text-sm font-medium">{chat.file?.title || "File Upload"}</div>
                    <div className="flex flex-wrap gap-2">
                      <FileUploadButton 
                        acceptedFileTypes="document"
                        onUploadSuccess={handleFileUploadSuccess} 
                      />
                      <FileUploadButton 
                        acceptedFileTypes="image"
                        onUploadSuccess={handleFileUploadSuccess} 
                      />
                    </div>
                  </div>
                )}
                
                <form onSubmit={handleSubmit} className="flex items-center">
                  <Textarea
                    ref={inputRef}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder={chat.input?.placeholder || chat.chat?.inputPlaceholder || "Ask me anything..."}
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
                      title={chat.file?.upload_image || chat.chat?.uploadImage || "Upload image"}
                      disabled={isLoading}
                      className={`text-primary/70 hover:text-primary hover:bg-primary/10 ${showFileManager ? 'bg-primary/10' : ''}`}
                      onClick={() => {
                        console.log("Upload button clicked, toggling file manager...");
                        setShowFileManager(!showFileManager);
                      }}
                      type="button"
                    >
                      <ImagePlus className="h-4 w-4" />
                      <span className="sr-only">{chat.file?.upload_image || chat.chat?.uploadImage || "Upload image"}</span>
                    </IconButton>
                    <IconButton
                      type="submit"
                      size="sm"
                      disabled={isLoading || !inputValue.trim()}
                      className="bg-gradient-to-r from-primary to-indigo-500 text-primary-foreground hover:opacity-90 shadow-sm hover:shadow-md hover:shadow-primary/10 transition-all"
                    >
                      <Send className="h-4 w-4" />
                      <span className="sr-only">{chat.chat?.send || "Send"}</span>
                    </IconButton>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}