# AI Assistant

A modern, extensible AI assistant platform with multi-modal capabilities and tool integration.

## Overview

AI Assistant is a full-stack application that provides an intelligent conversational interface powered by multiple language models. It features a clean, responsive UI, robust authentication, and modular tool integration through the Model Control Protocol (MCP).

## Key Features

- **Multi-LLM Support**: Seamlessly switch between OpenAI, Google Gemini, Anthropic Claude, and NVIDIA AI models
- **MCP Tool Integration**: Extend capabilities with specialized tools for math, weather, and more
- **Responsive Design**: Clean, intuitive interface that works across devices
- **Authentication System**: Secure user accounts and conversation management
- **Multilingual Support**: Interface available in English and Chinese
- **Real-time Chat**: Immediate responses with proper error handling

## System Architecture

The application follows a modern three-tier architecture:

- **Frontend**: Next.js with React and Tailwind CSS
- **Backend**: FastAPI Python service 
- **Database**: PostgreSQL for data persistence

## Installation

For detailed installation instructions, see the [Installation Manual](INSTALLATION.md).

Quick setup:

```bash
# Clone repository
git clone https://github.com/yourusername/ia-assiatant.git
cd ia-assiatant

# Setup backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Setup frontend
cd ../frontend
npm install
npm run dev
```

## MCP Tool Integration

The Model Control Protocol (MCP) allows the assistant to use specialized tools like:

- **Math Tool**: Evaluate complex mathematical expressions
- **Weather Tool**: Retrieve weather information for locations
- **Test Scenario Generator**: Generate test scripts from API specifications

To use these tools, start the MCP server in addition to the main backend:

```bash
cd backend
uvicorn mcp_server:app --reload --host 0.0.0.0 --port 8001
```

## Usage

1. Access the frontend at http://localhost:3000
2. Create an account or log in
3. Start a new conversation
4. Enter queries that might utilize tools or general knowledge

Example tool-based queries:
- "Calculate 123 multiplied by 456"
- "What's the weather in New York today?"

## Development

### Directory Structure

```
ia-assiatant/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── routers/
│   │   ├── services/
│   │   └── tools/
│   ├── mcp_server.py
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── context/
│   │   ├── dictionaries/
│   │   ├── hooks/
│   │   └── lib/
│   └── package.json
└── README.md
```

### Configuration

- Backend settings are managed through environment variables in `.env`
- Frontend environment settings are in `.env.local`
- MCP tool configuration is in `backend/app/config/mcp_tools.json`

## License

[MIT License](LICENSE)

## Acknowledgments

- Built with modern web technologies and AI services
- Uses LangChain for model integrations
- MCP adapters for extensible tool support 