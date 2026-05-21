"""OpenAI-backed decision engine."""

from __future__ import annotations

import json
import os

from dotenv import load_dotenv
from pydantic import ValidationError

from altinet.context.schemas import DecisionResponse


def decide_action_with_openai(prompt: str, *, model: str = "gpt-4o-mini") -> DecisionResponse:
    """Call OpenAI and validate strict JSON output against DecisionResponse."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to your .env file.")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    try:
        response = client.responses.create(
            model=model,
            input=prompt,
            text={"format": {"type": "json_object"}},
        )
        payload = json.loads(response.output_text)
        return DecisionResponse.model_validate(payload)
    except ValidationError as exc:
        raise RuntimeError(f"OpenAI returned JSON that does not match DecisionResponse: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("OpenAI did not return valid JSON.") from exc
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"OpenAI decision call failed: {exc}") from exc
