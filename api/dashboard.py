from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
from database.session import AsyncSessionLocal
from services.user_service import UserService
from services.meal_service import MealService
from services.gamification_service import GamificationService
from api.auth import verify_telegram_web_app_data

router = APIRouter(prefix="/api")

class GoalUpdateRequest(BaseModel):
    initData: str
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    daily_goal_kcal: Optional[float] = None

@router.get("/dashboard")
async def get_dashboard(initData: str):
    user_data = verify_telegram_web_app_data(initData)
    if not user_data:
        raise HTTPException(status_code=401, detail="Telegram WebApp avtorizatsiyasi muvaffaqiyatsiz bo'ldi")

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
            "height_cm": user.height_cm
        },
        "today_stats": today_stats,
        "weekly_stats": weekly_stats,
        "today_meals": meals_list,
        "badges": badges
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
