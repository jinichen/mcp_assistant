import React from 'react';
import ReactMarkdown from 'react-markdown';
import { formatReadableText } from '@/lib/utils';

const ChatMessage: React.FC<{ message: { content: string } }> = ({ message }) => {
  return (
    <div className="message-content text-formatter">
      {message.content && (
        <ReactMarkdown>{formatReadableText(message.content)}</ReactMarkdown>
      )}
    </div>
  );
};

export default ChatMessage; 