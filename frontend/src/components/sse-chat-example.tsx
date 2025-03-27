import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

export default function SSEChatExample() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState('gemini-1.5-pro');
  
  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setResponse('');
    
    try {
      // Create SSE connection
      const response = await fetch('/api/sse-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          query,
          model: selectedModel 
        })
      });
      
      // Create a reader for the stream
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Failed to create stream reader');
      }
      
      const decoder = new TextDecoder();
      let buffer = '';
      let fullResponse = '';
      
      // Process the stream
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        // Decode the chunk
        const chunk = decoder.decode(value);
        buffer += chunk;
        
        // Split by SSE standard format
        const events = buffer.split('\n\n');
        buffer = events.pop() || '';
        
        // Process each event
        events.forEach(event => {
          if (event.startsWith('data: ')) {
            const content = event.replace('data: ', '').trim();
            if (content !== 'done') {
              fullResponse += content;
              setResponse(fullResponse);
            }
          }
          
          if (event.startsWith('event: end')) {
            setIsLoading(false);
          }
          
          if (event.startsWith('event: error')) {
            console.error('SSE error:', event);
            setIsLoading(false);
          }
        });
      }
    } catch (error) {
      console.error('Stream error:', error);
      setIsLoading(false);
    }
  };
  
  // Available models
  const models = [
    { id: 'gpt-3.5-turbo', name: 'OpenAI - GPT-3.5 Turbo' },
    { id: 'gpt-4o', name: 'OpenAI - GPT-4o' },
    { id: 'gemini-1.5-pro', name: 'Google - Gemini 1.5 Pro' },
    { id: 'gemini-2.0-pro-exp-02-05', name: 'Google - Gemini 2.0 Pro' },
    { id: 'nvidia-deepseek-r1', name: 'NVIDIA - DeepSeek R1' },
    { id: 'llama-3', name: 'NVIDIA - Llama 3.3 Nemotron' }
  ];

  return (
    <div className="max-w-2xl mx-auto p-4 space-y-4">
      <h1 className="text-2xl font-bold">Streaming Chat Example</h1>
      
      <div className="mb-4">
        <Select
          value={selectedModel}
          onValueChange={setSelectedModel}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select a model" />
          </SelectTrigger>
          <SelectContent>
            {models.map(model => (
              <SelectItem key={model.id} value={model.id}>
                {model.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      
      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask something..."
          disabled={isLoading}
          className="flex-1"
        />
        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Generating...' : 'Send'}
        </Button>
      </form>
      
      <div className="p-4 border rounded-md min-h-[200px] whitespace-pre-wrap">
        {response}
        {isLoading && <span className="animate-pulse ml-1">|</span>}
      </div>
    </div>
  );
} 