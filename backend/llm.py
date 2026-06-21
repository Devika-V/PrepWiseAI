import os
import json

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Free-tier note (check periodically - Google adjusts this over time):
# as of mid-2026, Gemini 2.5 Flash and 2.5 Flash-Lite are the most reliable
# free-tier models. If you hit rate limits, switching this one line to
# "gemini-2.5-flash-lite" gives you a higher daily request allowance at a
# slight quality trade-off.
MODEL_NAME = "gemini-2.5-flash"

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


def generate_text(prompt: str) -> str:
    """Plain free-form text generation - used for phrasing questions."""
    client = _get_client()
    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    return (response.text or "").strip()


def generate_json(prompt: str) -> dict:
    """
    Forces Gemini to return valid JSON (rather than hoping it does), using
    the API's built-in response_mime_type setting. Still wrapped in a
    try/except, because no LLM call should be trusted to be perfect 100% of
    the time - a single bad response should never crash the whole interview.
    """
    client = _get_client()
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    try:
        return json.loads(response.text)
    except (json.JSONDecodeError, TypeError):
        return {
            "score": 5.0,
            "feedback": "Could not read the AI's feedback clearly this time - your answer was still recorded.",
        }