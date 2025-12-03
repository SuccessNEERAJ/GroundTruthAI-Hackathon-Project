"""
LLM client module for interacting with Groq's Meta LLaMA model.
Handles API calls and response streaming.
"""

from typing import Optional
from groq import Groq
from config import get_groq_api_key, validate_groq_api_key, DEFAULT_MODEL_NAME


def call_llm(prompt: str, model: str = DEFAULT_MODEL_NAME, temperature: float = 0.7) -> str:
    """
    Call the Groq LLaMA model with a prompt and return the response.
    
    This function assumes PII is already masked before calling.
    It does NOT perform any masking/unmasking internally.
    
    Args:
        prompt: The complete prompt to send to the LLM (should be pre-masked).
        model: The model name to use (default: llama-3.3-70b-versatile).
        temperature: Sampling temperature (0.0 to 2.0).
    
    Returns:
        str: The complete response text from the LLM.
    
    Raises:
        RuntimeError: If GROQ_API_KEY is not set.
        Exception: If the API call fails.
    """
    # Validate API key
    validate_groq_api_key()
    api_key = get_groq_api_key()
    
    # Initialize Groq client
    client = Groq(api_key=api_key)
    
    try:
        # Create chat completion with streaming
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=temperature,
            max_completion_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
        )
        
        # Collect streamed response
        full_response = ""
        for chunk in completion:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                full_response += delta.content
        
        return full_response.strip()
    
    except Exception as e:
        raise Exception(f"Error calling Groq API: {str(e)}")


def call_llm_with_system(system_prompt: str, user_prompt: str, model: str = DEFAULT_MODEL_NAME, temperature: float = 0.7) -> str:
    """
    Call the Groq LLaMA model with separate system and user prompts.
    
    Args:
        system_prompt: The system instruction/context.
        user_prompt: The user's message.
        model: The model name to use.
        temperature: Sampling temperature.
    
    Returns:
        str: The complete response text from the LLM.
    
    Raises:
        RuntimeError: If GROQ_API_KEY is not set.
        Exception: If the API call fails.
    """
    # Validate API key
    validate_groq_api_key()
    api_key = get_groq_api_key()
    
    # Initialize Groq client
    client = Groq(api_key=api_key)
    
    try:
        # Create chat completion with streaming
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
            temperature=temperature,
            max_completion_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
        )
        
        # Collect streamed response
        full_response = ""
        for chunk in completion:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                full_response += delta.content
        
        return full_response.strip()
    
    except Exception as e:
        raise Exception(f"Error calling Groq API: {str(e)}")


if __name__ == "__main__":
    # Test the LLM client
    print("=== Testing Groq LLaMA Client ===\n")
    
    try:
        test_prompt = "What is the capital of France? Answer in one sentence."
        print(f"Prompt: {test_prompt}\n")
        
        response = call_llm(test_prompt)
        print(f"Response: {response}\n")
        
        print("✓ LLM client test successful!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nMake sure you have:")
        print("1. Created a .env file with GROQ_API_KEY=your_key")
        print("2. Installed the groq package: pip install groq")
