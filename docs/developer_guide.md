# Developer Guide - Multimodal Chat Application

This developer guide provides comprehensive information for understanding, maintaining, and extending the Multimodal Chat Application.

## System Architecture

The application is built with a modern stack consisting of:

- **Backend**: FastAPI (Python)
- **Frontend**: React with Next.js (TypeScript)
- **API Communication**: REST API with JSON
- **Multimodal Processing**: Support for text and image content
- **LLM Integration**: OpenAI, Google Gemini, NVIDIA AI, Anthropic Claude models
- **Tool Integration**: MCP (Machine Conversation Protocol) for tool integration

### Project Structure

```
/
├── backend/                 # FastAPI backend
│   ├── app/                 # Application code
│   │   ├── api/             # API endpoints
│   │   ├── models/          # Data models for LLMs
│   │   ├── routes/          # Route handlers
│   │   └── services/        # Business logic and services
│   ├── uploads/             # Directory for uploaded images
│   └── main.py              # Entry point
├── frontend/                # Next.js frontend
│   ├── src/                 # Source code
│   │   ├── app/             # Next.js app router
│   │   ├── components/      # UI components
│   │   └── lib/             # Utilities and API clients
├── config/                  # Configuration files
│   └── mcp_config.json      # MCP services configuration
└── mcp-servers/             # MCP tool servers
```

## Backend Components

### ChatService (chat_service.py)

The core service handling chat interactions and model integration. Key responsibilities:

- Managing conversations with different LLMs
- Processing multimodal messages (text & images)
- Integration with MCP tools
- Streaming responses 
- Error handling and fallbacks

#### Multimodal Support

The service detects models with multimodal capabilities through:

1. Environment variable configuration (`MULTIMODAL_*_MODELS`)
2. Model name pattern matching
3. Special handling for multimodal messages

```python
# Example multimodal support check
def _check_multimodal_support(self, model: str) -> bool:
    # Get multimodal supported models from environment variables
    vision_models = os.getenv("MULTIMODAL_OPENAI_MODELS", "").split(",")
    gemini_vision_models = os.getenv("MULTIMODAL_GOOGLE_MODELS", "").split(",")
    nvidia_vision_models = os.getenv("MULTIMODAL_NVIDIA_MODELS", "").split(",")
    
    # Clean whitespace
    vision_models = [m.strip() for m in vision_models if m.strip()]
    gemini_vision_models = [m.strip() for m in gemini_vision_models if m.strip()]
    nvidia_vision_models = [m.strip() for m in nvidia_vision_models if m.strip()]
    
    # Check if model is in any multimodal support list
    if (model in vision_models or 
        model in gemini_vision_models or 
        model in nvidia_vision_models):
        return True
    
    # Also check for specific model prefixes
    if (model.startswith("gpt-4-vision") or 
        model.startswith("gpt-4o") or 
        model.startswith("gemini") or 
        "vision" in model.lower()):
        return True
        
    return False
```

### Upload Service (upload.py)

Handles image uploads with the following features:

- Image validation
- Automatic resizing for large images
- Base64 encoding for direct use in messages
- Secure file storage

### MCP Integration

The application integrates with MCP (Machine Conversation Protocol) to provide tool capabilities:

- Dynamic tool loading from configuration
- Tool execution through MCP servers
- Custom MCP client integration with LangGraph

## Frontend Components

### API Client (api.ts)

Handles all communication with the backend, including:

- Chat completion requests
- Image uploads
- Model selection
- Session management

### ImageUpload Component

Provides the user interface for uploading and previewing images:

- Drag and drop support
- Multiple image selection
- Preview before sending
- Error handling

### ChatMessage Component

Renders chat messages with support for:

- Text formatting with Markdown
- Image display
- Streaming text
- Tool call displays

## API Endpoints

### Chat Endpoints

- `POST /api/chat/completions`: Process chat completion requests
- `POST /api/chat/completions/stream`: Stream chat completion responses

### Upload Endpoints

- `POST /api/upload/images`: Upload and process images for chat

### Models Endpoint

- `GET /api/models`: Get available models and default model

## Integration Guide

### Adding a New Model Provider

1. Update the `.env` file with the new provider's API key and models
2. Add the new provider to `_get_llm` method in `chat_service.py`
3. Implement streaming support if needed
4. Update the frontend model selection to include the new provider

### Supporting a New Tool via MCP

1. Create a new MCP server implementing the tool functionality
2. Add the tool configuration to `config/mcp_config.json`
3. Restart the backend to load the new tool configuration

### Adding Custom Streaming Logic

The streaming implementation is in the `_stream_*_chat` methods in `chat_service.py`. To customize:

1. Modify the chunking logic for specific model characteristics
2. Adjust the delay for different streaming speeds
3. Update the response format if needed

## Environment Configuration

The application uses environment variables for configuration:

### API Keys

```
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
NVIDIA_API_KEY=your_nvidia_key
ANTHROPIC_API_KEY=your_anthropic_key
```

### Model Configuration

```
DEFAULT_MODEL=gemini-2.5-pro-exp-03-25
DEFAULT_PROVIDER=google

# Available models by provider
GOOGLE_MODELS=gemini-2.5-pro-exp-03-25,gemini-1.5-pro,gemini-1.5-flash
OPENAI_MODELS=gpt-4o-mini,gpt-3.5-turbo,gpt-4-turbo
NVIDIA_MODELS=meta/llama-3.3-70b-instruct,deepseek-ai/deepseek-r1,qwen/qwq-32b
ANTHROPIC_MODELS=claude-3-opus-20240229,claude-3-sonnet-20240229

# Multimodal models
MULTIMODAL_OPENAI_MODELS=gpt-4-vision-preview,gpt-4o,gpt-4-turbo,gpt-4-vision
MULTIMODAL_GOOGLE_MODELS=gemini-1.0-pro-vision,gemini-1.5-pro,gemini-1.5-flash,gemini-2.5-pro-exp-03-25
MULTIMODAL_NVIDIA_MODELS=llava,llava-13b,llava-7b
```

## Deployment

### Backend Deployment

1. Install dependencies: `pip install -r requirements.txt`
2. Set up environment variables
3. Run the server: `uvicorn main:app --host 0.0.0.0 --port 8000`

### Frontend Deployment

1. Install dependencies: `npm install`
2. Build the project: `npm run build`
3. Start the server: `npm start`

## Testing

The application can be tested using:

1. Unit tests for individual components
2. Integration tests for API endpoints
3. End-to-end tests for user flows

## Troubleshooting

Common issues and solutions:

1. **API Key Issues**: Ensure all required API keys are properly set in the environment
2. **MCP Configuration**: Verify the MCP config file is correctly formatted and accessible
3. **Model Compatibility**: Check if the selected model supports tools or multimodal inputs
4. **Image Upload Issues**: Ensure the uploads directory exists and has proper permissions
5. **Streaming Problems**: Debug by checking logs for chunking or response format issues

## Performance Considerations

- Large image files are automatically resized to improve performance
- Streaming uses incremental content delivery to enhance user experience
- Delays are added to streaming for better text flow visualization
- Tool execution is handled asynchronously for responsive UI 