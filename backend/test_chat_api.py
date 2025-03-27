import asyncio
import httpx
import json
from uuid import UUID
from fastapi.testclient import TestClient
from app.main import app
import pytest
import os
import uuid
from dotenv import load_dotenv

async def test_chat_api():
    base_url = "http://localhost:8000/api"
    
    async with httpx.AsyncClient() as client:
        # Test creating a session
        print("Creating session...")
        create_response = await client.post(
            f"{base_url}/sessions",
            json={
                "name": "Test Session",
                "provider": "google",
                "model": "gemini-2.0-pro-exp-02-05",
                "system_message": "You are a helpful assistant."
            }
        )
        create_data = create_response.json()
        print(f"Session created: {create_data}")
        
        session_id = create_data["id"]
        
        # Test sending a message
        print("\nSending message...")
        message_response = await client.post(
            f"{base_url}/chat",
            json={
                "session_id": session_id,
                "message": "What is the capital of France?",
                "parameters": {
                    "temperature": 0.7
                }
            }
        )
        message_data = message_response.json()
        print(f"Response received: {message_data}")
        
        # Test getting session list
        print("\nGetting session list...")
        sessions_response = await client.get(f"{base_url}/sessions")
        sessions_data = sessions_response.json()
        print(f"Sessions: {sessions_data}")
        
        # Test getting providers list
        print("\nGetting provider list...")
        providers_response = await client.get(f"{base_url}/providers")
        providers_data = providers_response.json()
        print(f"Providers: {providers_data}")
        
        # Test getting models list
        print("\nGetting model list...")
        models_response = await client.get(f"{base_url}/models")
        models_data = models_response.json()
        print(f"Models: {models_data}")

# Test creating a session
def test_create_session():
    client = TestClient(app)
    response = client.post("/api/chat/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "created_at" in data
    assert "messages" in data
    assert len(data["messages"]) == 0
    return data["session_id"]

# Test sending a message
def test_send_message():
    client = TestClient(app)
    session_id = test_create_session()
    
    message = {
        "role": "user",
        "content": "Hello, how are you?"
    }
    
    response = client.post(f"/api/chat/sessions/{session_id}/messages", json=message)
    assert response.status_code == 200
    data = response.json()
    assert "role" in data
    assert data["role"] == "assistant"
    assert "content" in data

# Test getting session list
def test_get_sessions():
    client = TestClient(app)
    response = client.get("/api/chat/sessions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

# Test getting providers list
def test_get_providers():
    client = TestClient(app)
    response = client.get("/api/chat/providers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

# Test getting models list
def test_get_models():
    client = TestClient(app)
    response = client.get("/api/chat/models")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

if __name__ == "__main__":
    asyncio.run(test_chat_api())