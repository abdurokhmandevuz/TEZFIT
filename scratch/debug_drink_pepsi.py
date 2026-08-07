import asyncio
import os
import httpx
import logging
from dotenv import load_dotenv

load_dotenv()
from config import settings
from services.ai_service import AIService, DRINK_VISION_PROMPT, VISION_MODELS

async def debug_all_models():
    async with httpx.AsyncClient() as client:
        r = await client.get("https://images.unsplash.com/photo-1629203851122-3726ecdf080e?w=500")
        img_bytes = r.content

    base64_image = AIService.compress_image(img_bytes, max_size=800)
    image_url = f"data:image/jpeg;base64,{base64_image}"

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://t.me/Tezfitbot",
        "X-Title": "TezFIT Drink Analyzer",
        "Content-Type": "application/json"
    }

    logs = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        for model in VISION_MODELS:
            payload = {
                "model": model,
                "max_tokens": 400,
                "temperature": 0.2,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": DRINK_VISION_PROMPT},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ]
            }
            try:
                res = await client.post(f"{settings.OPENROUTER_BASE_URL}/chat/completions", headers=headers, json=payload)
                logs.append(f"Model: {model} -> Status: {res.status_code}")
                if res.is_success:
                    content = res.json()["choices"][0]["message"]["content"]
                    logs.append(f"Content: {repr(content)}")
                    parsed = AIService._parse_json_response(content)
                    logs.append(f"Parsed: {repr(parsed)}")
                else:
                    logs.append(f"Error text: {res.text}")
            except Exception as e:
                logs.append(f"Model: {model} -> Exception: {e}")

    with open("scratch/pepsi_debug.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(logs))

if __name__ == "__main__":
    asyncio.run(debug_all_models())
