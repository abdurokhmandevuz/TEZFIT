import os
import httpx
from PIL import Image
import io
import base64
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("OPENROUTER_API_KEY")

img = Image.new("RGB", (100, 100), color="blue")
buf = io.BytesIO()
img.save(buf, format="JPEG")
b64 = base64.b64encode(buf.getvalue()).decode()

models = [
    "google/gemma-3-12b-it",
    "google/gemma-3-4b-it",
    "google/gemini-2.5-flash-lite",
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "openrouter/free"
]

prompt = "Analyze this drink image. Respond ONLY with clean JSON: {\"drink_name\": \"Pepsi\", \"calories\": 150, \"sugar_g\": 38.0, \"sugar_level\": \"38g\", \"is_halal\": true, \"halal_status\": \"Halol\", \"health_assessment\": \"Zararli\", \"details\": \"Pepsi\", \"volume_ml\": 330}"

client = httpx.Client(timeout=4.0)

for m in models:
    payload = {
        "model": m,
        "max_tokens": 200,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]
            }
        ]
    }
    try:
        res = client.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {key}"}, json=payload)
        print(f"{m} -> STATUS {res.status_code}")
        if res.status_code == 200:
            print("  SUCCESS:", res.json()["choices"][0]["message"]["content"][:100])
        else:
            print("  ERROR:", res.json().get("error", {}).get("message", "")[:100])
    except Exception as e:
        print(f"{m} -> TIMEOUT/ERR:", e)
