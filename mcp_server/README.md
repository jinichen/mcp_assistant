# MCP Server Tools

This directory contains various tool implementations for the Model Control Protocol (MCP) framework.

## Available Tools

- **Math**: Mathematical calculation tool
- **Weather**: Weather information retrieval tool
- **TestScenarioGenerator**: API test scenario generation tool
- **DuckDuckGo**: Web search tool

## Security and Configuration

### Sensitive Data

All sensitive data such as API keys should be stored in `.env` files. These files are ignored by Git (via `.gitignore`) and should never be committed to the repository.

For each tool:
1. Copy the corresponding `.env.example` file to `.env`
2. Add your own API keys and configuration
3. Never commit the `.env` files

### Example setup for TestScenarioGenerator

```bash
cd TestScenarioGenerator
cp .env.example .env
# Edit the .env file with your actual API keys
```

## Usage

Each tool can be used individually for development or testing:

```bash
cd TestScenarioGenerator
python __init__.py
```

Or through the main MCP server:

```bash
cd ../backend
python mcp_server.py
```

## Adding New Tools

To add a new tool:

1. Create a new directory for your tool
2. Implement the tool following the MCP protocol
3. Add a `.env.example` file with placeholder values
4. Update the tool configuration in `backend/app/config/mcp_tools.json`

## Environment Variables

Each tool directory should contain:
- `.env.example`: Template with placeholder values
- `.env`: Actual configuration file (not committed to Git) 