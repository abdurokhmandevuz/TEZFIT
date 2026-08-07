import base64
from datetime import datetime, date as date_cls
from sqlalchemy import select, and_
from database.models import Meal
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from bot import bot

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

class SubmitReceiptRequest(BaseModel):
    initData: str = ""
    plan_type: str = "monthly"
    amount_som: float = 29000
    receipt_b64: str = ""


@router.get("/dashboard")
async def get_dashboard_data(initData: str = "", date: Optional[str] = None):
    user_data = verify_telegram_web_app_data(initData)
    telegram_id = user_data["id"] if user_data and "id" in user_data else 123456789

    tg_first_name = user_data.get("first_name") if user_data else None
    tg_last_name = user_data.get("last_name") if user_data else None
    tg_username = user_data.get("username") if user_data else None
    tg_photo_url = user_data.get("photo_url") if user_data else None

    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(
            session=session,
            telegram_id=telegram_id,
            username=tg_username,
            name=f"{tg_first_name or ''} {tg_last_name or ''}".strip() if tg_first_name else None,
            first_name=tg_first_name,
            last_name=tg_last_name,
            photo_url=tg_photo_url
        )

        today_stats = await MealService.get_today_stats(session, user.id)
        weekly_stats = await MealService.get_weekly_stats(session, user.id)

        if date:
            try:
                t_date = date_cls.fromisoformat(date)
                day_start = datetime.combine(t_date, datetime.min.time())
                day_end = datetime.combine(t_date, datetime.max.time())
                stmt = select(Meal).where(
                    and_(Meal.user_id == user.id, Meal.created_at >= day_start, Meal.created_at <= day_end)
                ).order_by(Meal.created_at.desc())
                res = await session.execute(stmt)
                today_meals = list(res.scalars().all())
            except Exception:
                today_meals = await MealService.get_today_meals(session, user.id)
        else:
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
        contact_info = user.phone_number if (getattr(user, "phone_number", None) and "8817446491" not in user.phone_number) else f"ID: {user.telegram_id}"

        from config import settings
        free_limit = settings.USER_FREE_DAILY_LIMIT
        used_today = user.free_requests_today if user.last_request_date == date_cls.today() else 0
        remaining_scans = -1 if user.is_vip else max(0, free_limit - used_today)

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
            "dob": getattr(user, "dob", "2003-05-21"),
            "daily_goal_kcal": user.daily_goal_kcal,
            "is_vip": user.is_vip,
            "streak_days": user.streak_days,
            "points": getattr(user, "points", 100),
            "level": getattr(user, "level", 1),
            "weight_kg": user.weight_kg,
            "height_cm": user.height_cm,
            "age": user.age,
            "gender": user.gender or "Male",
            "remaining_scans": remaining_scans,
            "free_limit": free_limit
        },
        "today_stats": today_stats,
        "weekly_stats": weekly_stats,
        "today_meals": meals_list,
        "badges": badges
    }

@router.post("/profile")
async def update_profile_data(body: ProfileUpdateRequest):
    user_data = verify_telegram_web_app_data(body.initData)
    telegram_id = user_data["id"] if user_data and "id" in user_data else 123456789

    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(session, telegram_id)
        
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
    telegram_id = user_data["id"] if user_data and "id" in user_data else 123456789

    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(session, telegram_id)
        allowed, remaining = await UserService.check_and_increment_limit(session, user)

    if not allowed:
        return {
            "status": "limit_reached",
            "message": "Bugungi 15 ta tekin skan limiti tugadi! Cheksiz skan qilish uchun TezFIT Premium-ga o'ting 👑",
            "remaining": 0
        }

    image_bytes = await file.read()
    parsed_data = await AIService.analyze_food_image(image_bytes, is_vip=user.is_vip)
    return {"status": "success", "data": parsed_data, "remaining": remaining}

@router.post("/scan-text")
async def scan_text(body: ScanTextRequest):
    user_data = verify_telegram_web_app_data(body.initData)
    telegram_id = user_data["id"] if user_data and "id" in user_data else 123456789

    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(session, telegram_id)
        allowed, remaining = await UserService.check_and_increment_limit(session, user)

    if not allowed:
        return {
            "status": "limit_reached",
            "message": "Bugungi 15 ta tekin skan limiti tugadi! Cheksiz skan qilish uchun TezFIT Premium-ga o'ting 👑",
            "remaining": 0
        }

    parsed_data = await AIService.analyze_food_text(body.text, is_vip=user.is_vip)
    return {"status": "success", "data": parsed_data, "remaining": remaining}

@router.post("/save-meal")
async def save_meal_from_app(body: SaveMealRequest):
    user_data = verify_telegram_web_app_data(body.initData)
    telegram_id = user_data["id"] if user_data and "id" in user_data else 123456789

    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(session, telegram_id)
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

    # Send meal notification to user in Telegram Bot
    try:
        if user.telegram_id and user.telegram_id > 1000:
            total_cal = round(today_stats['total_calories'])
            goal_cal = round(user.daily_goal_kcal)
            bot_msg = (
                f"🍽 **YANGI TAOM SAQLANDI!**\n\n"
                f"📌 **Taom:** {meal.food_name}\n"
                f"⚖️ **Vazni:** {meal.weight_g}g\n"
                f"🔥 **Kaloriya:** {round(meal.calories)} kcal\n\n"
                f"📊 **BJU Taqsimoti:**\n"
                f"• 🥩 Oqsil: {meal.protein_g}g\n"
                f"• 🥑 Yog': {meal.fat_g}g\n"
                f"• 🌾 Uglevod: {meal.carbs_g}g\n\n"
                f"🎯 **Bugungi Jami:** {total_cal} / {goal_cal} kcal"
            )
            await bot.send_message(chat_id=user.telegram_id, text=bot_msg, parse_mode="Markdown")
    except Exception as e:
        print("Bot meal notification error:", e)

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
    telegram_id = user_data["id"] if user_data and "id" in user_data else 123456789

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

@router.post("/submit-receipt")
async def submit_receipt(body: SubmitReceiptRequest):
    user_data = verify_telegram_web_app_data(body.initData)
    telegram_id = user_data["id"] if user_data and "id" in user_data else 123456789

    async with AsyncSessionLocal() as session:
        user = await UserService.get_or_create_user(session, telegram_id)

    plan_label = "Oylik Premium (29,000 so'm)" if body.plan_type == "monthly" else "Yillik Premium (299,000 so'm)"
    
    admin_msg = (
        f"💳 **YANGI PREMIUM TO'LOV CHEKI KELDI!**\n\n"
        f"👤 **Foydalanuvchi:** {user.name or user.first_name} (`{user.telegram_id}`)\n"
        f"📞 **Aloqa:** {getattr(user, 'phone_number', None) or 'Mavjud emas'}\n"
        f"📦 **Rejim:** {plan_label}\n"
        f"💰 **Summa:** {int(body.amount_som):,} so'm\n"
        f"⏰ **Vaqt:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"Quyidagi tugmalar orqali tasdiqlang yoki rad eting:"
    )
    
    approve_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ VIP Berish", callback_data=f"approve_vip_{user.telegram_id}_{body.plan_type}"),
                InlineKeyboardButton(text="❌ Rad Etish", callback_data=f"reject_vip_{user.telegram_id}")
            ]
        ]
    )

    try:
        if body.receipt_b64 and "," in body.receipt_b64:
            header, img_str = body.receipt_b64.split(",", 1)
            img_data = base64.b64decode(img_str)
            photo_file = BufferedInputFile(img_data, filename=f"receipt_{user.telegram_id}.jpg")
            await bot.send_photo(
                chat_id=7225597812,
                photo=photo_file,
                caption=admin_msg,
                parse_mode="Markdown",
                reply_markup=approve_kb
            )
        else:
            await bot.send_message(
                chat_id=7225597812,
                text=admin_msg,
                parse_mode="Markdown",
                reply_markup=approve_kb
            )
    except Exception as e:
        print("Admin notification error:", e)

    return {
        "status": "success",
        "message": "To'lov cheki adminga muvaffaqiyatli yuborildi!"
    }
