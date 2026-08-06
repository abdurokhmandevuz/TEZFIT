from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from database.session import AsyncSessionLocal
from services.user_service import UserService
from services.meal_service import MealService
from services.gamification_service import GamificationService
from services.ai_service import AIService
from api.auth import verify_telegram_web_app_data

router = APIRouter(prefix="/api", tags=["dashboard"])

class ScanTextRequest(BaseModel):
    initData: str = ""
    text: str

class SaveMealRequest(BaseModel):
    initData: str = ""
    food_name: str
    weight_g: float = 150
    calories: float
    protein_g: float = 0
    fat_g: float = 0
    carbs_g: float = 0
    meal_time: Optional[str] = "snack"

class GoalUpdateRequest(BaseModel):
    initData: str = ""
    daily_goal_kcal: Optional[float] = None
    weight_kg: Optional[float] = None

class ProfileUpdateRequest(BaseModel):
    initData: str = ""
    name: Optional[str] = None
    phone_number: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None

@router.get("/dashboard")
async def get_dashboard_data(initData: str = ""):
    user_data = verify_telegram_web_app_data(initData)
    if not user_data:
        user_data = {"id": 123456789, "first_name": "Foydalanuvchi", "last_name": "", "username": "tezfit_user"}

    telegram_id = user_data["id"]
    tg_first_name = user_data.get("first_name", "")
    tg_last_name = user_data.get("last_name", "")
    tg_username = user_data.get("username", "")
    tg_photo_url = user_data.get("photo_url", "")

    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(session, telegram_id)

        # Update Telegram user info if missing
        updated = False
        if tg_first_name and not getattr(user, "first_name", None):
            user.first_name = tg_first_name
            updated = True
        if tg_last_name and not getattr(user, "last_name", None):
            user.last_name = tg_last_name
            updated = True
        if tg_photo_url and not getattr(user, "photo_url", None):
            user.photo_url = tg_photo_url
            updated = True
        if updated:
            await session.commit()

        today_stats = await MealService.get_today_stats(session, user.id)
        weekly_stats = await MealService.get_weekly_stats(session, user.id)
        today_meals = await MealService.get_today_meals(session, user.id)
        badges = await GamificationService.get_user_badges(session, user.id)

        meals_list = []
        for m in today_meals:
            meals_list.append({
                "id": m.id,
                "food_name": m.food_name,
                "weight_g": m.weight_g,
                "calories": m.calories,
                "protein_g": m.protein_g,
                "fat_g": m.fat_g,
                "carbs_g": m.carbs_g,
                "time": m.created_at.strftime("%H:%M") if m.created_at else "Bugun"
            })

        display_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.name or user.username or "Foydalanuvchi"
        contact_info = user.phone_number if getattr(user, "phone_number", None) else f"ID: {user.telegram_id}"

    return {
        "status": "success",
        "user": {
            "telegram_id": user.telegram_id,
            "name": display_name,
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "username": user.username or "",
            "phone_number": getattr(user, "phone_number", None) or f"ID: {user.telegram_id}",
            "photo_url": getattr(user, "photo_url", None) or "",
            "contact_info": contact_info,
            "dob": getattr(user, "dob", "2000-01-01"),
            "daily_goal_kcal": user.daily_goal_kcal,
            "is_vip": user.is_vip,
            "streak_days": user.streak_days,
            "points": getattr(user, "points", 100),
            "level": getattr(user, "level", 1),
            "weight_kg": user.weight_kg,
            "height_cm": user.height_cm,
            "age": user.age,
            "gender": user.gender or "Male"
        },
        "today_stats": today_stats,
        "weekly_stats": weekly_stats,
        "today_meals": meals_list,
        "badges": badges
    }

@router.post("/profile")
async def update_profile_data(body: ProfileUpdateRequest):
    user_data = verify_telegram_web_app_data(body.initData)
    if not user_data:
        user_data = {"id": 123456789, "first_name": "Foydalanuvchi"}

    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(session, user_data["id"])
        
        if body.name:
            user.name = body.name
            parts = body.name.split(" ", 1)
            user.first_name = parts[0]
            if len(parts) > 1:
                user.last_name = parts[1]
        if body.phone_number:
            user.phone_number = body.phone_number
        if body.dob:
            user.dob = body.dob
        if body.gender:
            user.gender = body.gender
        if body.height_cm:
            user.height_cm = body.height_cm
        if body.weight_kg:
            user.weight_kg = body.weight_kg

        await session.commit()
        await session.refresh(user)

    return {
        "status": "success",
        "user": {
            "telegram_id": user.telegram_id,
            "name": f"{user.first_name or ''} {user.last_name or ''}".strip() or user.name or "Foydalanuvchi",
            "phone_number": getattr(user, "phone_number", None) or f"ID: {user.telegram_id}",
            "gender": user.gender,
            "height_cm": user.height_cm,
            "weight_kg": user.weight_kg
        }
    }

@router.post("/scan-photo")
async def scan_photo(initData: str = Form(""), file: UploadFile = File(...)):
    user_data = verify_telegram_web_app_data(initData)
    if not user_data:
        user_data = {"id": 123456789, "first_name": "Foydalanuvchi"}

    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(session, user_data["id"])
        allowed, remaining = await UserService.check_and_increment_limit(session, user)

    image_bytes = await file.read()
    parsed_data = await AIService.analyze_food_image(image_bytes, is_vip=user.is_vip)
    return {"status": "success", "data": parsed_data, "remaining": remaining}

@router.post("/scan-text")
async def scan_text(body: ScanTextRequest):
    user_data = verify_telegram_web_app_data(body.initData)
    if not user_data:
        user_data = {"id": 123456789, "first_name": "Foydalanuvchi"}

    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(session, user_data["id"])
        allowed, remaining = await UserService.check_and_increment_limit(session, user)

    parsed_data = await AIService.analyze_food_text(body.text, is_vip=user.is_vip)
    return {"status": "success", "data": parsed_data, "remaining": remaining}

@router.post("/save-meal")
async def save_meal_from_app(body: SaveMealRequest):
    user_data = verify_telegram_web_app_data(body.initData)
    if not user_data:
        user_data = {"id": 123456789, "first_name": "Foydalanuvchi"}

    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(session, user_data["id"])
        meal = await MealService.add_meal(
            session=session,
            user_id=user.id,
            food_name=body.food_name,
            weight_g=body.weight_g,
            calories=body.calories,
            protein_g=body.protein_g,
            fat_g=body.fat_g,
            carbs_g=body.carbs_g,
            meal_time=body.meal_time or "snack"
        )
        streak, _ = await GamificationService.update_user_streak(session, user)
        today_stats = await MealService.get_today_stats(session, user.id)
        badges = await GamificationService.check_all_achievements(
            session, user, today_stats["total_calories"]
        )

    return {
        "status": "success",
        "meal_id": meal.id,
        "streak_days": streak,
        "today_stats": today_stats,
        "new_badges": badges
    }

@router.post("/goals")
async def update_goals(body: GoalUpdateRequest):
    user_data = verify_telegram_web_app_data(body.initData)
    if not user_data:
        user_data = {"id": 123456789, "first_name": "Foydalanuvchi"}

    telegram_id = user_data["id"]

    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(session, telegram_id)
        user = await UserService.update_profile(
            session=session,
            user=user,
            daily_goal_kcal=body.daily_goal_kcal,
            weight_kg=body.weight_kg
        )

    return {
        "status": "success",
        "daily_goal_kcal": user.daily_goal_kcal,
        "weight_kg": user.weight_kg
    }
