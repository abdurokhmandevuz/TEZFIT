import uuid
from typing import Dict, Any, Optional

# In-memory store for pending meal confirmations
# key: temp_id (str) -> value: Dict[str, Any]
PENDING_MEALS: Dict[str, Any] = {}

def create_pending_meal(user_id: int, parsed_data: Dict[str, Any], photo_file_id: Optional[str] = None) -> str:
    temp_id = str(uuid.uuid4())[:8]

    items = parsed_data.get("items", [])
    total_cal = parsed_data.get("total_calories", 0)

    # Aggregate item macros
    food_name = ", ".join([item.get("name", "Ovqat") for item in items]) or "Noma'lum ovqat"
    total_weight = sum([float(item.get("weight_g", 0)) for item in items])
    total_protein = sum([float(item.get("protein_g", 0)) for item in items])
    total_fat = sum([float(item.get("fat_g", 0)) for item in items])
    total_carbs = sum([float(item.get("carbs_g", 0)) for item in items])
    
    if total_cal <= 0 and items:
        total_cal = sum([float(item.get("calories", 0)) for item in items])

    PENDING_MEALS[temp_id] = {
        "user_id": user_id,
        "food_name": food_name,
        "weight_g": total_weight or 100.0,
        "calories": total_cal or 0.0,
        "protein_g": total_protein or 0.0,
        "fat_g": total_fat or 0.0,
        "carbs_g": total_carbs or 0.0,
        "photo_file_id": photo_file_id,
        "items": items
    }
    return temp_id

def get_pending_meal(temp_id: str) -> Optional[Dict[str, Any]]:
    return PENDING_MEALS.get(temp_id)

def remove_pending_meal(temp_id: str):
    if temp_id in PENDING_MEALS:
        del PENDING_MEALS[temp_id]
