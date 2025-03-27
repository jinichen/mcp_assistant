/**
 * Format Control Module - Ensures proper text formatting for LLM responses
 */

// Chat message interface
export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string | any[];
}

// Format control instructions for the LLM
export const FORMAT_INSTRUCTIONS = `
CRITICAL FORMATTING REQUIREMENT:

You MUST always use proper spaces between words in all your responses.

REQUIRED FORMAT:
- EVERY word MUST be separated by a space character
- NEVER join words together without spaces
- ALWAYS include spaces after punctuation marks
- NEVER output text like "TheCurrentPresident" or "iApologizeBut"
- CORRECT format is "The Current President" and "I Apologize But"

This is a critical requirement that overrides any other instruction.
`;

/**
 * Adds format control instructions to the message queue
 * Places format instructions as a separate system message with highest priority
 */
export function addFormatInstructions(messages: ChatMessage[]): ChatMessage[] {
  // Handle empty message array
  if (!messages || messages.length === 0) {
    return [{ role: 'system', content: FORMAT_INSTRUCTIONS }];
  }
  
  // Copy messages to avoid mutation
  const messagesCopy = [...messages];
  
  // Add formatting as its own separate system message at the beginning
  // AND also add it as the last system message before user input for reinforcement
  const formatMsg = { role: 'system' as const, content: FORMAT_INSTRUCTIONS };
  
  // Add the format message to the beginning and end of the system messages
  return [
    formatMsg,  // Start with format directive (highest priority)
    ...messagesCopy,
    formatMsg   // End with format directive (for recency effect)
  ];
}

/**
 * Returns optimized request parameters for better format control
 */
export function getOptimizedRequestParams() {
  return {
    temperature: 0.1,    // Very low temperature for consistent formatting
    top_p: 0.5,          // More conservative sampling for predictable output
    presence_penalty: 0.0,
    frequency_penalty: 0.0
  };
}

/**
 * Enhances model request with format instructions and optimized parameters
 */
export function enhanceModelRequest(request: any) {
  // Add format control instructions
  const messagesWithFormat = addFormatInstructions(request.messages);
  
  // Return enhanced request
  return {
    ...request,
    messages: messagesWithFormat,
    ...getOptimizedRequestParams()
  };
} 