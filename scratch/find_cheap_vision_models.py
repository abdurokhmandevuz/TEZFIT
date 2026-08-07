import os
import httpx
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("OPENROUTER_API_KEY")

res = httpx.get("https://openrouter.ai/api/v1/models")
data = res.json()

print("All models count:", len(data.get("data", [])))

vision_models = []
for m in data.get("data", []):
    m_id = m.get("id", "")
    arch = m.get("architecture", {})
    modalities = arch.get("input_modalities", [])
    if "image" in modalities:
        price = m.get("pricing", {})
        prompt_p = float(price.get("prompt", 0))
        vision_models.append((m_id, prompt_p))

print("Vision models count:", len(vision_models))
print("Free/Cheapest Vision models:")
for vid, price in sorted(vision_models, key=lambda x: x[1])[:20]:
    print(f" - {vid} (price: {price})")
