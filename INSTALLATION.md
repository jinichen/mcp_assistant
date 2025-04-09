# Installation Manual for AI Assistant

This guide covers how to set up and run the complete AI Assistant application, including database, backend, and frontend.

## Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- Git

## 1. Database Setup

### PostgreSQL Installation

#### For macOS:
```bash
brew install postgresql@14
brew services start postgresql@14
```

#### For Ubuntu/Debian:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Create Database and User

```bash
sudo -u postgres psql

# In PostgreSQL prompt
CREATE DATABASE ai_assistant;
CREATE USER ai_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE ai_assistant TO ai_user;
\q
```

## 2. Backend Setup

### Clone Repository
```bash
git clone https://github.com/your_username/ia-assiatant.git
cd ia-assiatant/backend
```

### Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Environment Configuration
Create a `.env` file in the backend directory:

```
# Database
DATABASE_URL=postgresql://ai_user:your_secure_password@localhost/ai_assistant

# API Settings
API_V1_STR=/api/v1
SECRET_KEY=your_secure_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# LLM Providers
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=https://api.openai.com/v1
DEFAULT_OPENAI_MODEL=gpt-4

# Optional: Google, Anthropic, NVIDIA
GOOGLE_API_KEY=your_google_key
DEFAULT_GOOGLE_MODEL=gemini-1.5-pro

ANTHROPIC_API_KEY=your_anthropic_key
DEFAULT_ANTHROPIC_MODEL=claude-3-opus-20240229

NVIDIA_API_KEY=your_nvidia_key
NVIDIA_BASE_URL=your_nvidia_endpoint
DEFAULT_NVIDIA_MODEL=llama2-70b
```

### Run Database Migrations
```bash
alembic upgrade head
```

### Start Backend Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 3. Frontend Setup

### Navigate to Frontend Directory
```bash
cd ../frontend
```

### Install Dependencies
```bash
npm install
```

### Environment Configuration
Create a `.env.local` file in the frontend directory:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

### Start Development Server
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`.

## 4. Verifying Installation

1. Open a browser and navigate to `http://localhost:3000`
2. The login page should appear
3. Create a new user or log in with the default credentials:
   - Username: admin
   - Password: admin (if you've set up a default admin user)
4. Test the chat functionality with one of the configured LLM providers

## 5. Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running: `pg_isready`
- Check connection string in `.env` file
- Ensure database user has proper permissions

### Backend Errors
- Check logs for detailed error messages
- Verify all environment variables are set correctly
- Ensure LLM API keys are valid

### Frontend Issues
- Clear browser cache and refresh
- Check browser console for JavaScript errors
- Verify the API base URL points to your running backend

## 6. Production Deployment

For production deployment, additional steps are recommended:
- Use a production WSGI server like Gunicorn
- Set up Nginx as a reverse proxy
- Configure SSL certificates
- Set proper CORS settings
- Use environment-specific configuration

## 7. MCP Tool Integration

To enable the MCP (Model Control Protocol) tools functionality:

1. Start the MCP server (separate from the main backend):
```bash
cd backend
uvicorn mcp_server:app --reload --host 0.0.0.0 --port 8001
```

2. Ensure tool scripts are properly located:
   - Math tool: `app/tools/math/math_server.py`
   - Weather tool: `app/tools/weather/weather_server.py`
   - Test generator: `app/tools/TestScenarioGenerator`

3. Tool configuration is in `app/config/mcp_tools.json`

4. When sending chat requests, the system will automatically route appropriate requests to specialized tools. 