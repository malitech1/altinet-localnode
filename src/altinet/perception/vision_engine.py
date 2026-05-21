"""Optional OpenAI vision second-stage analysis for room images."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError

from altinet.context.schemas import RoomContextResponse

DEFAULT_OPENAI_VISION_MODEL = "gpt-4.1-mini"


def _build_vision_prompt() -> str:
    return (
        "Analyse this room image and return ONLY strict JSON that matches this schema exactly: "
        "{"
        '"room_type_guess": "bedroom|kitchen|living_room|office|bathroom|unknown", '
        '"visible_people": ["..."], '
        '"visible_pets": ["..."], '
        '"visible_devices": ["..."], '
        '"lights_on": true|false|null, '
        '"lighting_description": "...", '
        '"notable_objects": ["..."], '
        '"safety_concerns": ["..."], '
        '"summary": "..."'
        "}. "
        "Do not include markdown, comments, or extra keys. Use empty arrays when unsure."
    )


def analyse_room_image_with_openai(image_path: Path) -> RoomContextResponse:
    """Extract structured room context from an image using a vision-capable OpenAI model."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. OpenAI vision is unavailable. "
            "Add OPENAI_API_KEY to .env, or run `python -m altinet.main observe-room` for local-only analysis."
        )

    if not image_path.exists():
        raise RuntimeError(f"Image not found: {image_path}")

    model = os.getenv("OPENAI_VISION_MODEL", DEFAULT_OPENAI_VISION_MODEL)

    with image_path.open("rb") as fh:
        image_b64 = base64.b64encode(fh.read()).decode("ascii")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    try:
        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": _build_vision_prompt()},
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
