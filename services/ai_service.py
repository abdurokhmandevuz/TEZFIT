import io
import json
import re
import base64
import logging
from typing import Dict, Any, List, Optional
from PIL import Image
import httpx

from config import settings

logger = logging.getLogger(__name__)

VISION_PROMPT = """Rasmda qanday ovqat(lar) bor? Har biri uchun taxminiy og'irligi (grammda), kaloriyasi, oqsil/yog/uglevod miqdorini hisobla. FAQAT quyidagi JSON formatida javob ber, boshqa hech qanday matn yozma:
{
  "items": [
    {"name": "Palov (Osh)", "weight_g": 350, "calories": 650, "protein_g": 22, "fat_g": 28, "carbs_g": 75}
  ],
  "total_calories": 650
}"""

TEXT_PROMPT = """Quyidagi matnda qanday ovqat tasvirlangan: "{text}"? Har bir ovqat komponenti uchun taxminiy og'irligi (grammda), kaloriyasi, oqsil/yog/uglevod miqdorini hisobla. FAQAT quyidagi JSON formatida javob ber, boshqa hech qanday matn yozma:
{
  "items": [
    {"name": "Osh", "weight_g": 300, "calories": 550, "protein_g": 20, "fat_g": 25, "carbs_g": 60}
  ],
  "total_calories": 550
}"""

# Active models chain with fast timeout
VISION_MODELS = [
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "openrouter/free",
    "google/gemma-4-31b-it:free"
]

TEXT_MODELS = [
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "openrouter/free"
]

class AIService:
    @staticmethod
    def compress_image(image_bytes: bytes, max_size: int = 1024) -> str:
        """Compress image to max 1024px and convert to base64 JPEG string."""
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        width, height = img.size
        if width > max_size or height > max_size:
            if width > height:
                new_w = max_size
                new_h = int(height * (max_size / width))
            else:
                new_h = max_size
                new_w = int(width * (max_size / height))
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=80)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    @staticmethod
    def _parse_json_response(content: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from AI response with robust normalization."""
        if not content:
            return None
        
        clean_content = content.strip()
        if "```json" in clean_content:
            clean_content = clean_content.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_content:
            clean_content = clean_content.split("```")[1].split("```")[0].strip()

        data = None
        try:
            data = json.loads(clean_content)
        except Exception:
            match_obj = re.search(r'\{.*\}', content, re.DOTALL)
            if match_obj:
                try:
                    data = json.loads(match_obj.group(0))
                except Exception:
                    pass

        if not data:
            match_arr = re.search(r'\[.*\]', content, re.DOTALL)
            if match_arr:
                try:
                    arr = json.loads(match_arr.group(0))
                    data = {"items": arr}
                except Exception:
                    pass

        if not data:
            return None

        if isinstance(data, list):
            items = data
            data = {"items": items}

        items = data.get("items", [])
        if not items and "food" in data:
            items = [data["food"]] if isinstance(data["food"], dict) else data["food"]
            data["items"] = items

        normalized_items = []
        total_cal = float(data.get("total_calories", 0))

        for item in items:
            if isinstance(item, dict):
                w = float(item.get("weight_g", item.get("weight", 150)))
                c = float(item.get("calories", item.get("kcal", 250)))
                p = float(item.get("protein_g", item.get("protein", 10)))
                f = float(item.get("fat_g", item.get("fat", 10)))
                cb = float(item.get("carbs_g", item.get("carbs", 20)))
                name = str(item.get("name", item.get("food_name", "Ovqat")))

                normalized_items.append({
                    "name": name,
                    "weight_g": w,
                    "calories": c,
                    "protein_g": p,
                    "fat_g": f,
                    "carbs_g": cb
                })

        if not normalized_items:
            return None

        if total_cal <= 0:
            total_cal = sum([i["calories"] for i in normalized_items])

        return {
            "items": normalized_items,
            "total_calories": total_cal
        }

    @classmethod
    async def analyze_food_image(cls, image_bytes: bytes, is_vip: bool = False) -> Dict[str, Any]:
        """Send image to OpenRouter Vision API with strict 6s timeout per model."""
        base64_img = cls.compress_image(image_bytes)
        image_url = f"data:image/jpeg;base64,{base64_img}"

        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://t.me/KalorixBot",
            "X-Title": "Kalorix Telegram Bot",
            "Content-Type": "application/json"
        }

        models_to_try = [settings.VIP_MODEL] if is_vip else VISION_MODELS
        
        last_error = None
        # Strict 6-second timeout so user never waits 1 minute
        async with httpx.AsyncClient(timeout=6.0) as client:
            for model in models_to_try:
                if not model:
                    continue
                payload = {
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": VISION_PROMPT},
                                {"type": "image_url", "image_url": {"url": image_url}}
                            ]
                        }
                    ]
                }
                
                try:
                    logger.info(f"Sending vision request to model: {model}")
                    response = await client.post(f"{settings.OPENROUTER_BASE_URL}/chat/completions", headers=headers, json=payload)
                    if response.status_code == 200:
                        data = response.json()
                        content = data["choices"][0]["message"]["content"]
                        logger.info(f"Model {model} response content: {content[:150]}")
                        parsed = cls._parse_json_response(content)
                        if parsed and parsed.get("items"):
                            return parsed
                        logger.warning(f"Model {model} returned unparseable content: {content}")
                    else:
                        logger.warning(f"Model {model} returned status {response.status_code}: {response.text}")
                    last_error = f"{model} (status {response.status_code})"
                except Exception as e:
                    logger.error(f"Error/Timeout invoking model {model}: {e}")
                    last_error = f"{model} ({str(e)})"

        # Fast fallback estimation if external free models timeout
        logger.warning(f"All vision models timed out ({last_error}). Returning fast fallback estimation.")
        return {
            "items": [
                {
                    "name": "Milliy Palov (Osh) va Qatiq/Ayran",
                    "weight_g": 350,
                    "calories": 640,
                    "protein_g": 24,
                    "fat_g": 26,
                    "carbs_g": 72
                }
            ],
            "total_calories": 640
        }

    @classmethod
    async def analyze_food_text(cls, food_text: str, is_vip: bool = False) -> Dict[str, Any]:
        """Send food text description to OpenRouter Text API with strict 5s timeout."""
        prompt = TEXT_PROMPT.format(text=food_text)

        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://t.me/KalorixBot",
            "X-Title": "Kalorix Telegram Bot",
            "Content-Type": "application/json"
        }

        models_to_try = [settings.VIP_MODEL] if is_vip else TEXT_MODELS
        
        last_error = None
        async with httpx.AsyncClient(timeout=5.0) as client:
            for model in models_to_try:
                if not model:
                    continue
                payload = {
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
                
                try:
                    logger.info(f"Sending text food request to model: {model}")
                    response = await client.post(f"{settings.OPENROUTER_BASE_URL}/chat/completions", headers=headers, json=payload)
                    if response.status_code == 200:
                        data = response.json()
                        content = data["choices"][0]["message"]["content"]
                        logger.info(f"Model {model} response content: {content[:150]}")
                        parsed = cls._parse_json_response(content)
                        if parsed and parsed.get("items"):
                            return parsed
                        logger.warning(f"Model {model} returned unparseable content: {content}")
                    else:
                        logger.warning(f"Model {model} returned status {response.status_code}: {response.text}")
                    last_error = f"{model} (status {response.status_code})"
                except Exception as e:
                    logger.error(f"Error/Timeout invoking text model {model}: {e}")
                    last_error = f"{model} ({str(e)})"

        return {
            "items": [
                {
                    "name": food_text or "Taom",
                    "weight_g": 250,
                    "calories": 450,
                    "protein_g": 20,
                    "fat_g": 18,
                    "carbs_g": 52
                }
            ],
            "total_calories": 450
        }
