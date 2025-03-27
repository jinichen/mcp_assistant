import asyncio
import os
from dotenv import load_dotenv
from app.models.model_factory import ModelFactory
from app.models.llm_base import ChatMessage

# Load environment variables
load_dotenv()

async def test_model_factory():
    # Create model factory instance
    factory = ModelFactory()
    
    # Print available providers
    providers = factory.get_available_providers()
    print(f"Available providers: {providers}")
    
    # Print all available models
    all_models = factory.get_available_models()
    print("\nAvailable models by provider:")
    for provider, models in all_models.items():
        print(f"  {provider}: {models}")
    
    # Test Google model
    print("\nTesting Google model:")
    google_model = factory.get_model("google")
    messages = [ChatMessage(role="user", content="What is the capital of France?")]
    response = await google_model.generate(messages)
    print(f"Response: {response}")
    
    # Test NVIDIA model
    print("\nTesting NVIDIA model:")
    nvidia_model = factory.get_model("nvidia")
    messages = [ChatMessage(role="user", content="What is the capital of Japan?")]
    response = await nvidia_model.generate(messages)
    print(f"Response: {response}")

    # Test OpenAI model
    print("\nTesting OpenAI model:")
    openai_model = factory.get_model("openai")
    messages = [ChatMessage(role="user", content="What is the capital of Spain?")]
    response = await openai_model.generate(messages)
    print(f"Response: {response}")
    
    # Test default model
    print("\nTesting default model:")
    default_model = factory.get_default_model()
    messages = [ChatMessage(role="user", content="What is the distance between Earth and Moon?")]
    response = await default_model.generate(messages)
    print(f"Response: {response}")

if __name__ == "__main__":
    asyncio.run(test_model_factory())