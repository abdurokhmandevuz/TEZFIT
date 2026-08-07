import os
import httpx
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("OPENROUTER_API_KEY")

res = httpx.get("https://openrouter.ai/api/v1/models", headers={"Authorization": f"Bearer {key}"})
data = res.json()

free_vision = []
for m in data.get("data", []):
    m_id = m.get("id", "")
    if "free" in m_id:
        architecture = m.get("architecture", {})
        modality = m.get("modality", "")
        input_modalities = architecture.get("input_modalities", [])
        if "image" in input_modalities or "vision" in modality:
            free_vision.append(m_id)

print("Free vision models:", free_vision)
