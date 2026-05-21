import json
import logging
from typing import Any

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is required for GeminiClient")
            
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(self.model_name)
        logger.info("Initialized GeminiClient with model: %s", self.model_name)
        
    def _convert_messages(self, messages: list[dict[str, str]]) -> tuple[str | None, list[dict]]:
        """
        Convert OpenAI-style messages to Gemini format.
        Returns (system_instruction, contents)
        """
        system_instruction = None
        contents = []
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            
            if role == "system":
                # Gemini handles system instruction separately
                if system_instruction is None:
                    system_instruction = content
                else:
                    system_instruction += "\n\n" + content
            elif role == "user":
                contents.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                contents.append({"role": "model", "parts": [content]})
                
        return system_instruction, contents

    async def chat(self, messages: list[dict[str, str]], response_mime_type: str | None = None) -> str:
        """Send chat request to Gemini."""
        system_instruction, contents = self._convert_messages(messages)
        
        # Override model if system_instruction is present
        # genai.GenerativeModel takes system_instruction in constructor
        model = self.model
        if system_instruction:
            model = genai.GenerativeModel(
                self.model_name,
                system_instruction=system_instruction
            )
            
        config = GenerationConfig(
            temperature=0.4,
        )
        if response_mime_type:
            config.response_mime_type = response_mime_type
            
        try:
            response = await model.generate_content_async(
                contents=contents,
                generation_config=config,
            )
            return response.text
        except Exception as e:
            logger.error("Gemini API error: %s", e)
            raise e

    async def chat_json(self, messages: list[dict[str, str]]) -> dict[str, Any] | None:
        """Helper to get guaranteed JSON response."""
        response_text = await self.chat(messages, response_mime_type="application/json")
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Gemini JSON: %s. Raw: %s", e, response_text)
            return None

_gemini_client = None

def get_gemini_client() -> GeminiClient:
    global _gemini_client
    from app.config import settings
    if _gemini_client is None:
        _gemini_client = GeminiClient(
            api_key=settings.google_api_key,
            model=settings.gemini_model,
        )
    return _gemini_client
