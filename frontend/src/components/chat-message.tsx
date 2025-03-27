"use client"

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Loader2 } from 'lucide-react';
import { useParams } from 'next/navigation';

interface ChatMessageProps {
  message: any;
  isLoading?: boolean;
}

// Format message content to ensure proper text spacing
const formatContent = (content: string) => {
  if (!content) return '';
  
  // Simple logging for debugging
  console.log('Original content:', content);
  
  // Check if content already contains spaces
  if (content.includes(' ')) {
    // Content already has spaces, return as is
    return content;
  }
  
  // Use more reliable method to detect if word separation is needed: if longer than 20 chars without spaces, likely needs separation
  if (content.length > 20) {
    // English text processing: add spaces at uppercase/lowercase boundaries
    // Example: "HelloWorld" -> "Hello World"
    let result = content.replace(/([a-z])([A-Z])/g, '$1 $2');
    
    // Additional simple word separation processing: common words and punctuation
    const commonPatterns = [
      // Add spaces before and after common conjunctions
      { pattern: /([^\s])(and|or|but|for|with|in|on|at|to|by|of|from)([^\s])/gi, replacement: '$1 $2 $3' },
      // Add spaces after punctuation (if not followed by space)
      { pattern: /([.,;:!?])([^\s])/g, replacement: '$1 $2' },
      // Add spaces after these words
      { pattern: /(is|are|was|were|has|have|had|will|would|could|should)([^\s])/gi, replacement: '$1 $2' },
      // Add spaces before common prepositions
      { pattern: /([^\s])(in|on|at|by|to|for|with|from|about)/gi, replacement: '$1 $2' }
    ];
    
    // Apply patterns
    for (const {pattern, replacement} of commonPatterns) {
      result = result.replace(pattern, replacement);
    }
    
    // If no space changes, try using simple word boundary separation
    if (!result.includes(' ')) {
      // Try to separate based on common word boundaries (like capital letters)
      result = result.replace(/([A-Z][a-z]+)(?=[A-Z])/g, '$1 ');
    }
    
    console.log('Processed content:', result);
    return result;
  }
  
  // Content is short, might be a brief reply or command, return as is
  return content;
};

// Custom component renderers for Markdown
const MarkdownComponents = {
  p: (props: any) => <p style={{ 
    marginTop: '0.7em', 
    marginBottom: '0.7em', 
    maxWidth: '100%',
    letterSpacing: '0.05em',
    lineHeight: '1.8'
  }}>{props.children}</p>,
  h1: (props: any) => <h1 style={{ fontSize: '1.8em', fontWeight: 'bold', marginTop: '1.2em', marginBottom: '0.6em' }}>{props.children}</h1>,
  h2: (props: any) => <h2 style={{ fontSize: '1.5em', fontWeight: 'bold', marginTop: '1.1em', marginBottom: '0.5em' }}>{props.children}</h2>,
  h3: (props: any) => <h3 style={{ fontSize: '1.3em', fontWeight: 'bold', marginTop: '1em', marginBottom: '0.5em' }}>{props.children}</h3>,
  h4: (props: any) => <h4 style={{ fontSize: '1.2em', fontWeight: 'bold', marginTop: '0.9em', marginBottom: '0.5em' }}>{props.children}</h4>,
  ul: (props: any) => <ul style={{ marginTop: '0.7em', marginBottom: '0.7em', paddingLeft: '1.5em' }}>{props.children}</ul>,
  ol: (props: any) => <ol style={{ marginTop: '0.7em', marginBottom: '0.7em', paddingLeft: '1.5em' }}>{props.children}</ol>,
  li: (props: any) => <li style={{ marginTop: '0.3em', marginBottom: '0.3em' }}>{props.children}</li>,
  blockquote: (props: any) => <blockquote style={{ borderLeft: '4px solid #e5e7eb', paddingLeft: '1em', marginLeft: '0', marginTop: '0.7em', marginBottom: '0.7em', color: '#6b7280' }}>{props.children}</blockquote>,
  pre: (props: any) => <pre style={{ backgroundColor: 'rgba(0, 0, 0, 0.03)', padding: '1em', borderRadius: '0.5em', overflowX: 'auto', marginTop: '0.7em', marginBottom: '0.7em', border: '1px solid rgba(203, 213, 225, 0.4)' }}>{props.children}</pre>,
  code: (props: any) => {
    // Inline code vs block code
    const isInline = !props.className;
    return isInline ? 
      <code style={{ backgroundColor: 'rgba(0, 0, 0, 0.03)', padding: '0.2em 0.4em', borderRadius: '0.25em', fontSize: '0.9em' }}>{props.children}</code> :
      <code style={{ display: 'block', fontFamily: 'monospace' }}>{props.children}</code>;
  },
};

// Prepare content for display
const prepareContent = (message: any, isLoading: boolean, isUser: boolean) => {
  if (isLoading) {
    return <Loader2 style={{ 
      height: '22px', 
      width: '22px', 
      color: '#3b82f6', 
      animation: 'spin 1s linear infinite',
      opacity: 0.9 
    }} />;
  }

  if (!message.content) return null;

  // Handle multimodal content (text and images)
  if (Array.isArray(message.content)) {
    return (
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        gap: '12px',
        maxWidth: '100%'
      }}>
        {message.content.map((part: any, index: number) => {
          if (part.type === 'text') {
            return (
              <div key={index} style={{ 
                maxWidth: '100%',
                wordSpacing: '0.03em',
                letterSpacing: '0.05em',
                lineHeight: '1.8',
                textAlign: 'justify'
              }}>
                <ReactMarkdown 
                  remarkPlugins={[remarkGfm]}
                  components={MarkdownComponents}
                >
                  {formatContent(part.text)}
                </ReactMarkdown>
              </div>
            );
          } else if (part.type === 'image_url') {
            return (
              <div key={index} style={{ 
                borderRadius: '10px', 
                overflow: 'hidden', 
                boxShadow: '0 4px 16px rgba(0, 0, 0, 0.08)', 
                maxWidth: '520px',
                border: '1px solid rgba(203, 213, 225, 0.4)'
              }}>
                <img 
                  src={part.image_url.url || part.image_url} 
                  alt="Image content" 
                  style={{ 
                    width: '100%', 
                    height: 'auto', 
                    objectFit: 'contain', 
                    backgroundColor: 'white' 
                  }}
                />
              </div>
            );
          }
          return null;
        })}
      </div>
    );
  }

  // Text content - supports Markdown
  return (
    <div style={{ 
      wordSpacing: '0.05em',
      letterSpacing: '0.03em',
      whiteSpace: 'pre-wrap',
      wordBreak: 'break-word',
      color: '#334155',
      lineHeight: '1.8',
      fontSize: '15px',
      maxWidth: '100%',
      textAlign: 'justify',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif'
    }}>
      <ReactMarkdown 
        remarkPlugins={[remarkGfm]}
        components={MarkdownComponents}
      >
        {formatContent(message.content)}
      </ReactMarkdown>
    </div>
  );
};

export function ChatMessage({ message, isLoading = false }: ChatMessageProps) {
  const isUser = message.role === 'user';
  
  // Get current language
  const params = useParams();
  const locale = Array.isArray(params.locale) ? params.locale[0] : params.locale as string;
  
  return (
    <div style={{ 
      display: 'flex',
      alignItems: 'flex-start',
      gap: '16px',
      marginBottom: '22px',
      opacity: isLoading ? '0.7' : '1',
      transition: 'all 0.3s ease',
      transform: isLoading ? 'translateY(5px)' : 'translateY(0)',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      width: '100%'
    }}>
      {/* Container with max width to enforce line breaks */}
      <div style={{ 
        display: 'flex',
        flexDirection: isUser ? 'row-reverse' : 'row',
        gap: '16px',
        maxWidth: '80%',
        alignItems: 'flex-start'
      }}>
        {/* Avatar for assistant or user */}
        <div style={{ flexShrink: 0, marginTop: '4px' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '13px',
            fontWeight: 600,
            color: isUser ? '#3b82f6' : '#7c3aed',
            background: isUser 
              ? 'linear-gradient(135deg, #dbeafe, #bfdbfe)' 
              : 'linear-gradient(135deg, #ede9fe, #ddd6fe)',
            border: `1px solid ${isUser ? 'rgba(191, 219, 254, 0.6)' : 'rgba(221, 214, 254, 0.6)'}`,
            boxShadow: isUser 
              ? '0 4px 10px rgba(59, 130, 246, 0.15)' 
              : '0 4px 10px rgba(124, 58, 237, 0.12)'
          }}>
            {isUser ? (locale === 'zh-CN' ? '用户' : 'U') : 'AI'}
          </div>
        </div>
      
      {/* Message content */}
        <div style={{
          padding: '18px',
          borderRadius: '14px',
          boxShadow: isUser 
            ? '0 4px 15px rgba(59, 130, 246, 0.08)' 
            : '0 4px 15px rgba(0, 0, 0, 0.05)',
          border: '1px solid',
          borderColor: isUser ? 'rgba(191, 219, 254, 0.7)' : 'rgba(229, 231, 235, 0.7)',
          background: isUser 
            ? 'linear-gradient(to bottom right, #f0f7ff, #e6f0fd)' 
            : 'linear-gradient(to bottom right, #ffffff, #fafafa)',
          maxWidth: '100%',
          overflow: 'hidden'
        }}>
          {prepareContent(message, isLoading, isUser)}
            
          {/* Tool call section - simplified for now */}
          {message.tool_calls && message.tool_calls.length > 0 && (
            <div style={{ 
              marginTop: '16px', 
              paddingTop: '12px', 
              borderTop: '1px solid rgba(203, 213, 225, 0.4)'
            }}>
              <div style={{ 
                fontSize: '14px', 
                color: '#6b7280',
                fontStyle: 'italic',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}>
                <div style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: '#3b82f6',
                  animation: 'pulse 1.5s infinite'
                }}></div>
                {locale === 'zh-CN' ? 'AI助手正在使用工具...' : 'AI assistant is using tools...'}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}