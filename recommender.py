import json
import os
import re
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from models import Message, ChatResponse, Recommendation
from prompts import SYSTEM_PROMPT

_CATALOG_PATH = Path(__file__).parent / "catalog.json"
_catalog_text: str | None = None
_client: genai.Client | None = None


def _load_catalog() -> str:
    global _catalog_text
    if _catalog_text is None:
        data = json.loads(_CATALOG_PATH.read_text())
        _catalog_text = json.dumps(data, indent=2)
    return _catalog_text


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set.")
        _client = genai.Client(api_key=api_key)
    return _client


def _parse_response(raw: str) -> dict[str, Any]:
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


async def get_chat_response(messages: list[Message]) -> ChatResponse:
    client = _get_client()
    system_prompt = SYSTEM_PROMPT.format(catalog=_load_catalog())

    # Build contents list for the API
    contents: list[types.Content] = []
    for msg in messages:
        role = "user" if msg.role == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg.content)]))

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        response_mime_type="application/json",
        max_output_tokens=8192,
    )

    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=config,
    )

    raw = response.text or "{}"
    data = _parse_response(raw)

    recommendations = [
        Recommendation(
            name=r.get("name", ""),
            url=r.get("url", ""),
            test_type=r.get("test_type", ""),
        )
        for r in data.get("recommendations", [])
    ]

    return ChatResponse(
        reply=data.get("reply", ""),
        recommendations=recommendations,
        end_of_conversation=bool(data.get("end_of_conversation", False)),
    )
