# API Reference - Multimodal Chat Application

This document provides a comprehensive reference for the Multimodal Chat Application's API endpoints, request/response formats, and error handling.

## Base URL

All API endpoints are relative to the base URL of your deployment:

```
http://your-deployment-url/api
```

## Authentication

Currently, the API does not require authentication for local development. For production deployments, appropriate authentication mechanisms should be implemented.

## Endpoints

### Chat Completions

#### POST /chat/completions

Process a chat completion request.

**Request Body:**

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Hello world!"
    }
  ],
  "model": "gemini-2.5-pro-exp-03-25",
  "tools": [],
  "tool_choice": "auto"
}
```

**Response:**

```json
{
  "id": "chatcmpl-123456789",
  "object": "chat.completion",
  "created": 1625123422,
  "model": "gemini-2.5-pro-exp-03-25",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I assist you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  }
}
```

#### POST /chat/completions/stream

Stream a chat completion response.

**Request Body:**
Same as for `/chat/completions`.

**Response:**
Server-Sent Events (SSE) stream with the following format:

```
data: {"choices":[{"delta":{"content":"Hello"}}],"model":"gemini-2.5-pro-exp-03-25"}

data: {"choices":[{"delta":{"content":"! How"}}],"model":"gemini-2.5-pro-exp-03-25"}

data: {"choices":[{"delta":{"content":" can I assist"}}],"model":"gemini-2.5-pro-exp-03-25"}

data: {"choices":[{"delta":{"content":" you today?"}}],"model":"gemini-2.5-pro-exp-03-25"}
```

### Image Upload

#### POST /upload/images

Upload images for use in chat.

**Request Body:**
Form data with one or more files with the name `files`.

**Response:**

```json
{
  "images": [
    {
      "filename": "example.jpg",
      "content_type": "image/jpeg",
      "size": 12345,
      "image_url": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...",
      "file_path": "/uploads/12345-example.jpg"
    }
  ]
}
```

### Models

#### GET /models

Get available models.

**Query Parameters:**
- `provider` (optional): Filter models by provider (e.g., "google", "openai", "nvidia")

**Response:**

```json
{
  "models": {
    "google": [
      {
        "id": "gemini-2.5-pro-exp-03-25",
        "name": "Gemini 2.5 Pro"
      },
      {
        "id": "gemini-1.5-pro",
        "name": "Gemini 1.5 Pro"
      }
    ],
    "openai": [
      {
        "id": "gpt-4o",
        "name": "GPT-4o"
      }
    ]
  },
  "default": "gemini-2.5-pro-exp-03-25"
}
```

### Sessions

#### GET /sessions

List all saved chat sessions.

**Response:**

```json
{
  "sessions": [
    {
      "id": "sess_12345",
      "title": "My Chat Session",
      "created_at": "2023-06-15T14:22:31Z",
      "updated_at": "2023-06-15T14:30:12Z",
      "model": "gemini-2.5-pro-exp-03-25",
      "message_count": 8
    }
  ]
}
```

#### POST /sessions

Save a chat session.

**Request Body:**

```json
{
  "title": "My Chat Session",
  "model": "gemini-2.5-pro-exp-03-25",
  "messages": [
    {
      "role": "user",
      "content": "Hello world!"
    },
    {
      "role": "assistant",
      "content": "Hello! How can I assist you today?"
    }
  ]
}
```

**Response:**

```json
{
  "id": "sess_12345",
  "title": "My Chat Session",
  "created_at": "2023-06-15T14:22:31Z",
  "model": "gemini-2.5-pro-exp-03-25",
  "message_count": 2
}
```

#### GET /sessions/{session_id}

Get a specific chat session.

**Response:**

```json
{
  "id": "sess_12345",
  "title": "My Chat Session",
  "created_at": "2023-06-15T14:22:31Z",
  "updated_at": "2023-06-15T14:30:12Z",
  "model": "gemini-2.5-pro-exp-03-25",
  "messages": [
    {
      "role": "user",
      "content": "Hello world!"
    },
    {
      "role": "assistant",
      "content": "Hello! How can I assist you today?"
    }
  ]
}
```

#### DELETE /sessions/{session_id}

Delete a chat session.

**Response:**

```json
{
  "success": true,
  "message": "Session deleted successfully"
}
```

### Tools

#### POST /tools/execute

Execute a specific tool.

**Request Body:**

```json
{
  "name": "calculator",
  "arguments": {
    "expression": "15% of 85.99"
  }
}
```

**Response:**

```json
{
  "result": "12.8985"
}
```

## Multimodal Message Format

For sending messages with both text and images, use the following format:

```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What can you tell me about this image?"
        },
        {
          "type": "image",
          "image_url": {
            "url": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD..."
          }
        }
      ]
    }
  ],
  "model": "gemini-2.5-pro-exp-03-25"
}
```

## Error Handling

The API uses standard HTTP status codes for error responses:

- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Request validation error
- `500 Internal Server Error`: Server-side error

Error responses have the following format:

```json
{
  "error": {
    "message": "Detailed error message",
    "type": "error_type",
    "param": "parameter_name",
    "code": "error_code"
  }
}
```

## Rate Limiting

The API implements rate limiting to ensure fair usage. Rate limits are:

- 10 requests per minute for chat completions
- 20 requests per minute for model listing
- 5 requests per minute for image uploads

Rate limit headers are included in API responses:

- `X-RateLimit-Limit`: Total requests allowed in the period
- `X-RateLimit-Remaining`: Remaining requests in the period
- `X-RateLimit-Reset`: Time until the rate limit resets (in seconds)

## Versioning

The API is currently at version 1. The version is not included in the URL path but may be in future releases.

## Tools Reference

The following tools are available for use with compatible models:

### Calculator

Performs mathematical calculations.

**Parameters:**
- `expression` (string): The mathematical expression to evaluate

**Example:**
```json
{
  "name": "calculator",
  "arguments": {
    "expression": "sqrt(144) + 5"
  }
}
```

### DuckDuckGo Search

Searches the web for information.

**Parameters:**
- `query` (string): The search query

**Example:**
```json
{
  "name": "duckduckgo",
  "arguments": {
    "query": "latest news about renewable energy"
  }
}
```

### MCP Monitor

Monitors system status and resources.

**Parameters:**
- `command` (string): The monitoring command
- `resource` (string, optional): The specific resource to monitor

**Example:**
```json
{
  "name": "mcp_monitor",
  "arguments": {
    "command": "status",
    "resource": "cpu"
  }
}
``` 