import asyncio
import os
from dotenv import load_dotenv
from app.models.anthropic_model import AnthropicModel
from app.models.llm_base import ChatMessage

# Load environment variables
load_dotenv()

async def test_anthropic_model():
    # Create Anthropic model instance
    model = AnthropicModel()
    
    # Test messages
    messages = [
        ChatMessage(role="user", content="What is the capital of Italy?")
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
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
    else:
        asyncio.run(test_anthropic_model())