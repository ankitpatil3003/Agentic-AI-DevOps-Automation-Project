# app/integrations/llm_client.py

import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


class LLMClient:
    """
    Wrapper for OpenAI GPT calls.
    Supports simple chat completions.
    """

    @staticmethod
    def chat(prompt: str, model: str = "gpt-4", temperature: float = 0.2) -> str:
        """
        Send a single-turn chat completion to OpenAI.
        """
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )
            return response.choices[0].message.content.strip()

        except openai.OpenAIError as e:
            return f"[LLM Error] {str(e)}"
