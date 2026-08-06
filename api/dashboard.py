import logging
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from database.session import AsyncSessionLocal
from services.user_service import UserService
from services.meal_service import MealService
from services.gamification_service import GamificationService
from services.ai_service import AIService
from api.auth import verify_telegram_web_app_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

class GoalUpdateRequest(BaseModel):
    initData: str
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    daily_goal_kcal: Optional[float] = None

class ScanTextRequest(BaseModel):
    initData: str
    text: str

class SaveMealRequest(BaseModel):
    initData: str
    food_name: str
    weight_g: float
    calories: float
    protein_g: float
    fat_g: float
    carbs_g: float
    meal_time: Optional[str] = "snack"

@router.get("/dashboard")
async def get_dashboard(initData: str):
    user_data = verify_telegram_web_app_data(initData)
    if not user_data:
        raise HTTPException(status_code=401, detail="TezFIT avtorizatsiyasi muvaffaqiyatsiz bo'ldi")

    telegram_id = user_data["id"]

    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(
            session=session,
            telegram_id=telegram_id,
            username=user_data.get("username"),
            name=user_data.get("first_name")
        )
        today_stats = await MealService.get_today_stats(session, user.id)
        weekly_stats = await MealService.get_weekly_stats(session, user.id)
        today_meals = await MealService.get_today_meals(session, user.id)
        badges = await GamificationService.get_user_badges(session, user.id)

    meals_list = [
        {
            "id": m.id,
            "food_name": m.food_name,
            "weight_g": m.weight_g,
            "calories": m.calories,
            "protein_g": m.protein_g,
            "fat_g": m.fat_g,
            "carbs_g": m.carbs_g,
            "time": m.created_at.strftime("%H:%M")
        } for m in today_meals
    ]

    return {
        "user": {
            "telegram_id": user.telegram_id,
            "name": user.name or user_data.get("first_name", "Foydalanuvchi"),
            "username": user.username,
            "daily_goal_kcal": user.daily_goal_kcal,
            "streak_days": user.streak_days,
            "is_vip": user.is_vip,
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
async def scan_photo(initData: str = Form(...), file: UploadFile = File(...)):
    user_data = verify_telegram_web_app_data(initData)
    if not user_data:
        raise HTTPException(status_code=401, detail="Avtorizatsiya rad etildi")

    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(session, user_data["id"])
        allowed, remaining = await UserService.check_and_increment_limit(session, user)

    if not allowed:
        raise HTTPException(status_code=429, detail="Bugungi bepul so'rovlar me'yori tugadi. VIP statusga o'ting!")

    image_bytes = await file.read()
    parsed_data = await AIService.analyze_food_image(image_bytes, is_vip=user.is_vip)
    return {"status": "success", "data": parsed_data, "remaining": remaining}

@router.post("/scan-text")
async def scan_text(body: ScanTextRequest):
    user_data = verify_telegram_web_app_data(body.initData)
    if not user_data:
        raise HTTPException(status_code=401, detail="Avtorizatsiya rad etildi")

    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(session, user_data["id"])
        allowed, remaining = await UserService.check_and_increment_limit(session, user)

    if not allowed:
        raise HTTPException(status_code=429, detail="Bugungi bepul so'rovlar me'yori tugadi. VIP statusga o'ting!")

    parsed_data = await AIService.analyze_food_text(body.text, is_vip=user.is_vip)
    return {"status": "success", "data": parsed_data, "remaining": remaining}

@router.post("/save-meal")
async def save_meal_from_app(body: SaveMealRequest):
    user_data = verify_telegram_web_app_data(body.initData)
    if not user_data:
        raise HTTPException(status_code=401, detail="Avtorizatsiya rad etildi")

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
        raise HTTPException(status_code=401, detail="Avtorizatsiya rad etildi")

    telegram_id = user_data["id"]

    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(session, telegram_id)
        user = await UserService.update_profile(
            session=session,
            user=user,
            weight_kg=body.weight_kg,
            height_cm=body.height_cm,
            daily_goal_kcal=body.daily_goal_kcal
        )

    return {"status": "success", "daily_goal_kcal": user.daily_goal_kcal}
