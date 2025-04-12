# AI Assistant

## Overview
AI Assistant is a modern full-stack application with multi-modal capabilities, supporting multiple language models (LLMs) and tool integrations. It provides an intuitive interface for interacting with AI models and supports various specialized tools such as math calculations, weather queries, and more.

## Key Features
- **Multi-LLM Support**: Integration with OpenAI, Google, Anthropic, and NVIDIA models
- **MCP Tool Integration**: Specialized tools via the Model Control Protocol (MCP)
- **Responsive Design**: Modern UI for both desktop and mobile devices
- **Authentication System**: Secure user authentication and session management
- **Multilingual Support**: English and Chinese interfaces
- **Real-time Chat**: Fluid conversation experience
- **File Upload**: Document and image upload support for AI analysis and processing

## System Architecture
AI Assistant uses a three-tier architecture:

1. **Frontend**: React application built with Next.js
   - Responsive design with Tailwind CSS
   - Internationalization support
   - Real-time chat interface
   - File upload and management components

2. **Backend**: Python service using FastAPI
   - RESTful API
   - Multi-LLM integration
   - MCP tool management
   - User authentication
   - File upload handling

3. **Database**: PostgreSQL
   - User management
   - Session storage
   - Tool configurations
   - File metadata storage

## Installation
Quick start:
```bash
# Clone the repository
git clone https://github.com/yourusername/ia-assistant.git
cd ia-assistant

# Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup frontend
cd ../frontend
npm install
```

For detailed installation instructions, refer to the [Installation Guide](INSTALLATION.md).

## MCP Tool Integration
AI Assistant integrates various specialized tools through the Model Control Protocol (MCP):

### Available Tools
- **Math Tool**: Perform mathematical calculations
- **Weather Tool**: Retrieve weather information
- **More Tools**: Continuously being integrated...

### Start MCP Server
```bash
cd backend
python mcp_server.py
```

## File Upload Feature
AI Assistant supports uploading various file formats:

### Supported File Types
- **Documents**: PDF, DOCX, TXT, MD, CSV, JSON
- **Images**: JPG, JPEG, PNG, GIF, BMP, WEBP

### How to Use
1. Click the upload button in the chat interface
2. Select the file type (document or image)
3. Choose a file from your local storage
4. Once uploaded, the file will appear in the chat, and the AI can analyze its content

## Usage Guide
1. Access the frontend: `http://localhost:3000`
2. Create an account or log in
3. Start chatting, for example:
   - "Calculate 123 + 456"
   - "What's the weather in New York?"
   - "Use the math tool to calculate 789 * 321"
   - "Upload a file and analyze its content"

## Development
### Directory Structure
```
ia-assistant/
├── backend/           # FastAPI backend service
│   ├── app/          # Application code
│   ├── tests/        # Test files
│   └── requirements.txt
├── frontend/         # Next.js frontend application
│   ├── src/         # Source code
│   ├── public/      # Static assets
│   └── package.json
└── README.md        # Project documentation
```

### Configuration
#### Backend Configuration
In `backend/.env`:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/ia_assistant
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
```

#### Frontend Configuration
In `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements
Thanks to the following technologies and services:
- Next.js and React
- FastAPI
- PostgreSQL
- AI services from OpenAI, Google, Anthropic, and NVIDIA
- Tailwind CSS 