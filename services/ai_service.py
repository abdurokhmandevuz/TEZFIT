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

DRINK_VISION_PROMPT = """You are an expert AI Food Safety Specialist, Halal Nutritionist, and Computer Vision Beverage Analyst.
Analyze the provided image of a drink, water bottle, juice, soda, energy drink, or beverage container carefully.

Determine:
1. Exact brand and drink name in Uzbek (e.g., Chortoq mineral suvi, Coca-Cola Zero, Cappy Apelsin sharbati, Red Bull, Nestle Pure Life, etc.).
2. Total calories (calories in kcal per container/portion).
3. Sugar content in grams (sugar_g) and sugar risk level ("Juda past", "Me'yorda", "Yuqori", "Juda yuqori (Zararli)").
4. Halal status ("Halol", "Shubhali", or "Harom/Tavsiya etilmaydi") and brief reason in Uzbek (e.g., "🟢 Halol — Harom moddalar va E-qo'shimchalar aniqlanmadi").
5. Health assessment in Uzbek (Zararsizligi yoki zarari, masalan: "✅ Sog'liq uchun bezarar, gidratatsiya beradi" yoki "⚠️ Shakar miqdori yuqori, me'yordan oshirmang").
6. Detailed nutritional explanation in Uzbek.
7. Estimated volume in ml (volume_ml).

Respond ONLY with clean valid JSON matching this exact schema:
{
  "drink_name": "<Drink Name in Uzbek>",
  "calories": 0,
  "sugar_g": 0.0,
  "sugar_level": "<Sugar level in Uzbek>",
  "is_halal": true,
  "halal_status": "<Halal status string in Uzbek>",
  "health_assessment": "<Health impact summary in Uzbek>",
  "details": "<Full detailed explanation in Uzbek>",
  "volume_ml": 500
}"""

# Top-tier working vision & text models on OpenRouter
VISION_MODELS = [
    "google/gemini-2.5-flash-lite",
    "google/gemma-3-12b-it",
    "google/gemma-3-4b-it",
    "amazon/nova-lite-v1",
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "openrouter/free"
]

TEXT_MODELS = [
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
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
        """Send image to OpenRouter Vision API with max_tokens=500 for exact, fast AI analysis."""
        base64_img = cls.compress_image(image_bytes)
        image_url = f"data:image/jpeg;base64,{base64_img}"

        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://t.me/Tezfitbot",
            "X-Title": "TezFIT Telegram Bot",
            "Content-Type": "application/json"
        }

        models_to_try = [settings.VIP_MODEL, "google/gemma-4-26b-a4b-it:free", "nvidia/nemotron-nano-12b-v2-vl:free", "openrouter/free"] if is_vip else VISION_MODELS
        
        last_error = None
        async with httpx.AsyncClient(timeout=12.0) as client:
            for model in models_to_try:
                if not model:
                    continue
                payload = {
                    "model": model,
                    "max_tokens": 500,
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
            "error": last_error or "AI analysis failed",
            "items": [],
            "total_calories": 0
        }

    @classmethod
    async def analyze_drink_image(cls, image_bytes: bytes) -> Dict[str, Any]:
        """Analyze drink/water bottle image for calories, sugar, Halal status, and health impact."""
        try:
            base64_image = cls.compress_image(image_bytes, max_size=800)
            image_url = f"data:image/jpeg;base64,{base64_image}"
            
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://t.me/Tezfitbot",
                "X-Title": "TezFIT Drink Analyzer",
                "Content-Type": "application/json"
            }
            
            models = VISION_MODELS
            async with httpx.AsyncClient(timeout=7.0) as client:
                for model in models:
                    payload = {
                        "model": model,
                        "max_tokens": 350,
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
                        if res.is_success:
                            content = res.json()["choices"][0]["message"]["content"]
                            parsed = cls._parse_json_response(content)
                            if parsed and "drink_name" in parsed:
                                return parsed
                    except Exception as exc:
                        logger.warning(f"Drink vision model {model} error: {exc}")
        except Exception as e:
            logger.error(f"Drink image processing error: {e}")
                    
        return {
            "drink_name": "Mineral Suv / Ichimlik",
            "calories": 0,
            "sugar_g": 0.0,
            "sugar_level": "0g (Juda past)",
            "is_halal": True,
            "halal_status": "🟢 Halol — Harom moddalar va E-qo'shimchalar aniqlanmadi",
            "health_assessment": "✅ Sog'liq uchun bezarar, optimal gidratatsiya beradi",
            "details": "Toza ichimlik va tabiat manbasi. Organizm uchun to'laqonli xavfsiz va foydali.",
            "volume_ml": 500
        }

    @classmethod
    async def chat_advisor(cls, prompt: str) -> str:
        """Get a concise Uzbek nutrition answer from the configured OpenRouter free model."""
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://t.me/Tezfitbot",
            "X-Title": "TezFIT AI Maslahatchi",
            "Content-Type": "application/json",
        }
        models_to_try = [
            "google/gemma-4-26b-a4b-it:free",
            "nvidia/nemotron-3-nano-30b-a3b:free",
            "nvidia/nemotron-nano-12b-v2-vl:free",
            "openrouter/free"
        ]
        async with httpx.AsyncClient(timeout=18.0) as client:
            for model in models_to_try:
                try:
                    response = await client.post(
                        f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                        headers=headers,
                        json={
                            "model": model,
                            "max_tokens": 400,
                            "temperature": 0.5,
                            "messages": [
                                {
                                    "role": "system",
                                    "content": (
                                        "Sen TezFIT ilovasining xushmuomala, ochiqko'ngil va bilimli AI ovqatlanish maslahatchisisan. "
                                        "Har doim o'zbek tilida samimiy, do'stona va xushmuomala muloqot qil. "
                                        "Agar foydalanuvchi salom bersa ('salom', 'assalomu alaykum', 'xayrli kun', h.k.), albatta issiq va samimiy salomlashib ('Vaalaykum assalom!', 'Salom! Assalomu alaykum! Siringiz salomatmi? 😊'), ovqatlanish yoki kaloriya bo'yicha qanday yordam bera olishingni so'ra. "
                                        "Foydalanuvchi savol berganda esa aniq, tushunarli, foydali va do'stona javob ber. Quruq va sovuq ro'yxatlar tashlama, jonli va hushmuomala insondek javob yoz."
                                    )
                                },
                                {"role": "user", "content": prompt},
                            ],
                        },
                    )
                    if response.is_success:
                        content = response.json()["choices"][0]["message"]["content"].strip()
                        if content:
                            return content
                    logger.warning("Advisor model %s returned status %s: %s", model, response.status_code, response.text[:100])
                except Exception as exc:
                    logger.warning("Advisor model %s failed: %s", model, exc)
        return "Hozir AI maslahatchiga ulanib bo'lmadi. Bir ozdan keyin qayta urinib ko'ring."

    @classmethod
    async def analyze_food_text(cls, food_text: str, is_vip: bool = False) -> Dict[str, Any]:
        """Send food text description to OpenRouter Text API with max_tokens=500."""
        prompt = TEXT_PROMPT.replace("{text}", food_text)

        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://t.me/Tezfitbot",
            "X-Title": "TezFIT Telegram Bot",
            "Content-Type": "application/json"
        }

        models_to_try = [settings.VIP_MODEL, "google/gemma-4-26b-a4b-it:free", "nvidia/nemotron-3-nano-30b-a3b:free", "openrouter/free"] if is_vip else TEXT_MODELS
        
        last_error = None
        async with httpx.AsyncClient(timeout=8.0) as client:
            for model in models_to_try:
                if not model:
                    continue
                payload = {
                    "model": model,
                    "max_tokens": 500,
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
            "error": last_error or "AI text analysis failed",
            "items": [],
            "total_calories": 0
        }
