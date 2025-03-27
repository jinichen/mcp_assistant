import asyncio
import os
from dotenv import load_dotenv
from app.models.openai_model import OpenAIModel
from app.models.llm_base import ChatMessage

# Load environment variables
load_dotenv()

async def test_openai_model():
    # Create OpenAI model instance
    model = OpenAIModel()
    
    # Test messages
    messages = [
        ChatMessage(role="user", content="What is the capital of Spain?")
    ]
    
    # Test generation
    print("Testing standard generation:")
    response = await model.generate(messages)
    print(f"Response: {response}")
    
    # Test streaming generation
    print("\nTesting streaming generation:")
    async for chunk in model.generate_stream(messages):
        print(chunk, end="", flush=True)
    print("\n\nStreaming completed")

if __name__ == "__main__":
    # Ensure API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
    else:
        asyncio.run(test_openai_model())