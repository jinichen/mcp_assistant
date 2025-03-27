/**
 * Send chat requests to the backend
 */
import { enhanceModelRequest, ChatMessage } from './format-control';

interface ChatCompletionRequestMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface ChatCompletionRequest {
  messages: ChatCompletionRequestMessage[];
  model: string;
  temperature?: number;
  tools?: any[];
}

const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

async function delay(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function fetchWithRetry(url: string, options: RequestInit, retries = MAX_RETRIES): Promise<Response> {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Connection': 'keep-alive',
        'Keep-Alive': 'timeout=60',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response;
  } catch (error) {
    if (retries > 0) {
      await delay(RETRY_DELAY);
      return fetchWithRetry(url, options, retries - 1);
    }
    throw error;
  }
}

export async function chatCompletion(request: ChatCompletionRequest) {
  try {
    // Use format control to enhance request
    const enhancedRequest = enhanceModelRequest(request);
    
    const response = await fetchWithRetry('/api/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(enhancedRequest),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error in chat completion:', error);
    throw error;
  }
}

/**
 * Execute tool calls
 */
export async function executeToolCall(toolName: string, args: any) {
  const response = await fetch(`/api/tools/${toolName}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(args),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to execute tool');
  }

  return response.json();
}

/**
 * Save a chat session
 */
export async function saveSession(title: string, model: string, messages: any[]) {
  const response = await fetch('/api/sessions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      title,
      model,
      messages,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to save session');
  }

  return await response.json();
}

/**
 * Get session list
 */
export async function listSessions(limit: number = 20, offset: number = 0) {
  const response = await fetch(`/api/sessions?limit=${limit}&offset=${offset}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get session list');
  }

  return await response.json();
}

/**
 * Get session details
 */
export async function getSession(sessionId: string) {
  const response = await fetch(`/api/sessions/${sessionId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get session details');
  }

  return await response.json();
}

/**
 * Delete session
 */
export async function deleteSession(sessionId: string) {
  const response = await fetch(`/api/sessions/${sessionId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete session');
  }

  return await response.json();
}

/**
 * Streaming chat completion with simplified interface
 */
export async function streamChatCompletion(messages: any[], model: string) {
  try {
    // Use format control to enhance request
    const enhancedRequest = enhanceModelRequest({
      messages,
      model,
      stream: true
    });
    
    const response = await fetch('/api/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(enhancedRequest),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // Process streaming response and accumulate complete content
    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Failed to get stream reader');
    }

    const decoder = new TextDecoder("utf-8");
    let content = '';
    let toolCalls: any[] = [];
    let lastChunk = '';

    console.log("==== Starting stream processing ====");

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      // Use utf-8 decode and preserve stream state
      const chunk = decoder.decode(value, { stream: true });
      console.log("Raw chunk received:", JSON.stringify(chunk));
      
      // Ensure data isn't lost across chunk boundaries
      const processText = lastChunk + chunk;
      const lines = processText.split('\n\n');
      
      // Save the last potentially incomplete line for next processing
      lastChunk = lines.pop() || '';
      
      for (const line of lines) {
        if (line.startsWith('data: ') && line.length > 6) {
          try {
            const dataStr = line.substring(6);
            console.log("Processing data:", JSON.stringify(dataStr));
            
            const data = JSON.parse(dataStr);
            if (data.content) {
              console.log("Content received:", JSON.stringify(data.content));
              content += data.content;
            }
            
            if (data.tool_calls && data.tool_calls.length > 0) {
              toolCalls = data.tool_calls;
            }
          } catch (e) {
            console.error('Error parsing chunk:', e, 'in line:', JSON.stringify(line));
          }
        }
      }
    }

    // Verify final content after stream processing is complete
    console.log("Final accumulated content:", JSON.stringify(content));

    return {
      content,
      tool_calls: toolCalls
    };
  } catch (error) {
    console.error('Error in streaming chat completion:', error);
    throw error;
  }
}

/**
 * Original streaming function (kept for backward compatibility)
 */
export function streamChatCompletionGenerator(request: ChatCompletionRequest) {
  return async function* () {
    try {
      // Use format control to enhance the request
      const enhancedRequest = enhanceModelRequest({
        ...request,
        stream: true
      });
      
      const response = await fetch('/api/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(enhancedRequest),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Failed to get stream reader');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;

        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.substring(6);
            
            // Skip empty data or "[DONE]" messages
            if (!data || data === '[DONE]') continue;
            
            try {
              const parsed = JSON.parse(data);
              yield parsed;
            } catch (e) {
              console.error('Error parsing JSON from stream:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error in streaming chat completion:', error);
      throw error;
    }
  };
}

/**
 * Get available models
 */
export async function getAvailableModels() {
  const response = await fetch('/api/models');

  if (!response.ok) {
    throw new Error('Failed to fetch available models');
  }
  
  const data = await response.json();
  
  // Format models data for UI
  const formattedModels = [];
  
  // Process models by provider
  for (const [provider, models] of Object.entries(data.models)) {
    // Skip if no models for this provider
    if (!Array.isArray(models) || models.length === 0) continue;
    
    // Map provider name to UI friendly name
    const providerNames: Record<string, string> = {
      'google': 'Google',
      'openai': 'OpenAI',
      'nvidia': 'NVIDIA',
      'anthropic': 'Anthropic'
    };
    
    // Add each model with provider prefix
    for (const model of models) {
      formattedModels.push({
        id: model,
        name: `${providerNames[provider] || provider} - ${model}`
      });
    }
  }
  
  return {
    models: formattedModels,
    // Use first model as default if available
    default: formattedModels.length > 0 ? formattedModels[0].id : null
  };
}

/**
 * Upload images to the server
 */
export async function uploadImages(files: File[]) {
  const formData = new FormData();
  
  // Append each file to the form data
  files.forEach(file => {
    formData.append('files', file);
  });
  
  const response = await fetch('/api/upload/images', {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to upload images');
  }
  
  return await response.json();
}