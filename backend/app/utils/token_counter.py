import tiktoken
from typing import List, Union

def count_tokens(text: Union[str, List[str]], model: str = "gpt-3.5-turbo") -> int:
    """Calculate the token count for text or a list of texts"""
    try:
        # Load encoder
        encoding = tiktoken.encoding_for_model(model)
        
        # Process text or list of texts
        if isinstance(text, str):
            return len(encoding.encode(text))
        elif isinstance(text, list):
            total_tokens = 0
            for item in text:
                if isinstance(item, str):
                    total_tokens += len(encoding.encode(item))
            return total_tokens
        else:
            return 0
    except Exception as e:
        print(f"Error counting tokens: {str(e)}")
        return 0