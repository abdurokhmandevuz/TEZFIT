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

@router.get("/dashboard")
async def get_dashboard_data(initData: str = ""):
    user_data = verify_telegram_web_app_data(initData)
    if not user_data:
        user_data = {"id": 123456789, "first_name": "Foydalanuvchi"}

    telegram_id = user_data["id"]

    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(session, telegram_id)
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

    return {
        "status": "success",
        "user": {
            "name": user.first_name or user.username or "Foydalanuvchi",
            "daily_goal_kcal": user.daily_goal_kcal,
            "is_vip": user.is_vip,
            "streak_days": user.streak_days,
            "points": user.points,
            "level": user.level,
            "weight_kg": user.weight_kg,
            "height_cm": user.height_cm,
            "age": user.age,
            "gender": user.gender
        },
        "today_stats": today_stats,
        "weekly_stats": weekly_stats,
        "today_meals": meals_list,
        "badges": badges
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
