import base64
import os
import requests

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

def describe_image_bytes(image_bytes: bytes, content_type: str) -> str:
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Describe this image for a blind person. "
                            "Explain the surroundings, layout, colors, objects, "
                            "any visible text, and their relative positions. "
                            "Use clear and calm language."
                        )
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{content_type};base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30
    )

    if response.status_code != 200:
        raise RuntimeError(response.text)

    return response.json()["choices"][0]["message"]["content"]
