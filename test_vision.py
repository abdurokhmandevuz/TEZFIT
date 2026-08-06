import os
import io
import base64
import httpx
from PIL import Image
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("OPENROUTER_API_KEY")

img = Image.new("RGB", (200, 200), color="red")
buf = io.BytesIO()
img.save(buf, format="JPEG")
b64 = base64.b64encode(buf.getvalue()).decode()

prompt = "Rasmda nima bor? FAQAT JSON formatida javob ber: {\"items\": [{\"name\": \"Ovqat\", \"weight_g\": 200, \"calories\": 300, \"protein_g\": 10, \"fat_g\": 10, \"carbs_g\": 30}], \"total_calories\": 300}"

models = ["nvidia/nemotron-nano-12b-v2-vl:free", "openrouter/free", "google/gemini-2.0-flash-001"]

client = httpx.Client(timeout=15.0)

for m in models:
    payload = {
        "model": m,
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
        print(f"MODEL {m} STATUS:", res.status_code)
        if res.status_code == 200:
            content = res.json()["choices"][0]["message"]["content"]
            print(f"MODEL {m} CONTENT:\n", repr(content))
        else:
            print(f"MODEL {m} ERROR:\n", res.text)
    except Exception as e:
        print(f"MODEL {m} EXCEPTION:", e)
