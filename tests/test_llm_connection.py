import os

import pytest
from dotenv import load_dotenv

from app.services.llm_client import GroqLLMClient


load_dotenv()


@pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY"),
    reason="GROQ_API_KEY is not configured",
)
def test_groq_connection():
    client = GroqLLMClient()

    result = client.generate(
        system_prompt="You are a helpful assistant.",
        user_prompt="Reply with exactly: GROQ_CONNECTION_OK",
    )

    assert "GROQ_CONNECTION_OK" in result