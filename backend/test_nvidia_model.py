import asyncio
import os
from dotenv import load_dotenv
from app.models.nvidia_model import NVIDIAModel
from app.models.llm_base import ChatMessage

# Load environment variables
load_dotenv()

async def test_nvidia_model():
    # Create NVIDIA model instance
    model = NVIDIAModel()
    
    # Test messages
    messages = [
        ChatMessage(role="user", content="What is the capital of Japan?")
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
    if not os.getenv("NVIDIA_API_KEY"):
        print("Error: NVIDIA_API_KEY environment variable not set")
    else:
        asyncio.run(test_nvidia_model())