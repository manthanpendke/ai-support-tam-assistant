import json
import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


class GroqLLMClient:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")

        self.model = os.getenv(
            "GROQ_MODEL",
            "llama-3.3-70b-versatile",
        )

        if not self.api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured. "
                "Add it to your local .env file."
            )

        self.client = Groq(
            api_key=self.api_key,
        )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False,
    ) -> str:

        request_kwargs = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        }

        if json_mode:
            request_kwargs["response_format"] = {
                "type": "json_object",
            }

        response = self.client.chat.completions.create(
            **request_kwargs
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "LLM returned an empty response."
            )

        return content
    def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
    ):
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            stream=True,
        )

        for chunk in response:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta
            content = delta.content

            if content:
                yield content

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:

        content = self.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=True,
        )

        try:
            result = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"LLM returned invalid JSON: {content}"
            ) from exc

        if not isinstance(result, dict):
            raise RuntimeError(
                "LLM JSON response must be an object."
            )

        return self._normalise_keys(result)

    @staticmethod
    def _normalise_keys(
        data: dict[str, Any],
    ) -> dict[str, Any]:

        key_mapping = {
            "PRODUCT": "product",
            "PRODUCT_AREA": "product_area",
            "CATEGORY": "category",
            "URGENCY": "urgency",
            "REASONING": "reasoning",
            "KNOWN_ISSUE": "known_issue",
            "KB_DOCUMENT": "kb_document",
            "RECOMMENDED_RESPONDER_TEAM": (
                "recommended_responder_team"
            ),
            "FIRST_RESPONSE": "first_response",
        }

        normalized = {}

        for key, value in data.items():
            normalized_key = key_mapping.get(
                key.strip().upper(),
                key.strip(),
            )

            normalized[normalized_key] = value

        return normalized