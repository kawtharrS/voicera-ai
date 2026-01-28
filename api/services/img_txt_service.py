import base64
import os

import requests

from config import HEADERS, TIMEOUT, MAX_TOKENS, OPENAI_API_URL, MODEL
from utils.img_promot import IMAGE_DESCRIPTION_PROMPT

def describe_image_bytes(image_bytes: bytes, content_type: str) -> str:
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": IMAGE_DESCRIPTION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{content_type};base64,{base64_image}"},
                    },
                ],
            }
        ],
        "max_tokens": MAX_TOKENS,
    }

    response = requests.post(
        OPENAI_API_URL,
        headers=HEADERS,
        json=payload,
        timeout=TIMEOUT,
    )

    response.raise_for_status()
    
    return response.json()["choices"][0]["message"]["content"]