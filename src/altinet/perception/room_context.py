"""OpenAI vision room-context extraction."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError

from altinet.context.schemas import RoomContextResponse


def analyse_room_image_with_openai(image_path: Path, *, model: str = "gpt-4.1-mini") -> RoomContextResponse:
    """Extract room context JSON from an image using a vision-capable OpenAI model."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to your .env file.")

    if not image_path.exists():
        raise RuntimeError(f"Image not found: {image_path}")

    with image_path.open("rb") as fh:
        image_b64 = base64.b64encode(fh.read()).decode("ascii")

    prompt = (
        "Describe the room context from this image and output strict JSON with keys: "
        "room_type_guess, visible_people, visible_pets, lights_on, notable_objects, "
        "safety_concerns, summary. lights_on must be true, false, or 'unknown'. "
        "visible_people/visible_pets/notable_objects/safety_concerns must be arrays of short strings."
    )

    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    try:
        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": f"data:image/jpeg;base64,{image_b64}"},
                    ],
                }
            ],
            text={"format": {"type": "json_object"}},
        )
        payload = json.loads(response.output_text)
        return RoomContextResponse.model_validate(payload)
    except ValidationError as exc:
        raise RuntimeError(f"OpenAI returned JSON that does not match RoomContextResponse: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("OpenAI did not return valid JSON.") from exc
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"OpenAI room-context call failed: {exc}") from exc
