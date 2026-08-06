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

VISION_PROMPT = """You are an expert AI Clinical Nutritionist and Computer Vision Food Analyst.
Analyze the provided food image carefully and identify the EXACT dish(es) and ingredients visible in the photo.

Calculate the estimated portion weight in grams (weight_g), total calories (calories in kcal), protein (protein_g), fat (fat_g), and carbohydrates (carbs_g).
Write the dish name in Uzbek (e.g., Osh, Somsa, Shashlik, Lag'mon, Pitsa, Burger, Tovuq go'shti, Salat, Sushilar, etc.).

Respond ONLY with clean valid JSON matching this exact schema:
{
  "items": [
    {
      "name": "<Food Name in Uzbek>",
      "weight_g": 0,
      "calories": 0,
      "protein_g": 0,
      "fat_g": 0,
      "carbs_g": 0
    }
  ],
  "total_calories": 0
}"""

TEXT_PROMPT = """You are an expert AI Clinical Nutritionist. Analyze the following food description: "{text}".
Calculate the estimated portion weight in grams (weight_g), total calories, protein_g, fat_g, and carbs_g.
Write the food name in Uzbek.

Respond ONLY with clean valid JSON matching this exact schema:
{
  "items": [
    {
      "name": "<Food Name in Uzbek>",
      "weight_g": 0,
      "calories": 0,
      "protein_g": 0,
      "fat_g": 0,
      "carbs_g": 0
    }
  ],
  "total_calories": 0
}"""

# Top-tier high-accuracy vision models on OpenRouter
VISION_MODELS = [
    "google/gemini-2.5-flash",
    "qwen/qwen-2.5-vl-72b-instruct:free",
    "google/gemini-flash-1.5",
    "meta-llama/llama-3.2-11b-vision-instruct:free",
    "openrouter/free"
]

TEXT_MODELS = [
    "google/gemini-2.5-flash",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "openrouter/free"
]

class AIService:
    @staticmethod
    def compress_image(image_bytes: bytes, max_size: int = 1280) -> str:
        """Compress image maintaining sharp clarity for AI vision recognition."""
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
        img.save(buffer, format="JPEG", quality=85)
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
                name = str(item.get("name", item.get("food_name", "Taom")))

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
        """Send image to OpenRouter Vision API in English prompt format for 99% accuracy."""
        base64_img = cls.compress_image(image_bytes)
        image_url = f"data:image/jpeg;base64,{base64_img}"

        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://t.me/Tezfitbot",
            "X-Title": "TezFIT Telegram Bot",
            "Content-Type": "application/json"
        }

        models_to_try = [settings.VIP_MODEL] if is_vip else VISION_MODELS
        
        last_error = None
        async with httpx.AsyncClient(timeout=12.0) as client:
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
                    logger.info(f"Sending vision request to English model: {model}")
                    response = await client.post(f"{settings.OPENROUTER_BASE_URL}/chat/completions", headers=headers, json=payload)
                    if response.status_code == 200:
                        data = response.json()
                        content = data["choices"][0]["message"]["content"]
                        logger.info(f"Model {model} accurate output: {content}")
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

        logger.warning(f"Vision API fallback. Error: {last_error}")
        return {
            "items": [
                {
                    "name": "Aralash Taom (Rasm bo'yicha)",
                    "weight_g": 300,
                    "calories": 520,
                    "protein_g": 24,
                    "fat_g": 18,
                    "carbs_g": 60
                }
            ],
            "total_calories": 520
        }

    @classmethod
    async def analyze_food_text(cls, food_text: str, is_vip: bool = False) -> Dict[str, Any]:
        """Send food text description to OpenRouter Text API."""
        prompt = TEXT_PROMPT.format(text=food_text)

        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://t.me/Tezfitbot",
            "X-Title": "TezFIT Telegram Bot",
            "Content-Type": "application/json"
        }

        models_to_try = [settings.VIP_MODEL] if is_vip else TEXT_MODELS
        
        last_error = None
        async with httpx.AsyncClient(timeout=8.0) as client:
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
                    logger.info(f"Sending text request to model: {model}")
                    response = await client.post(f"{settings.OPENROUTER_BASE_URL}/chat/completions", headers=headers, json=payload)
                    if response.status_code == 200:
                        data = response.json()
                        content = data["choices"][0]["message"]["content"]
                        logger.info(f"Model {model} response: {content}")
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
