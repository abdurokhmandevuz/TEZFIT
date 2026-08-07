import json
import asyncio
from datetime import datetime, date, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from .models import User, Meal, Achievement, Reminder
from services.ai_service import AIService
from api.auth import verify_telegram_web_app_data

def get_tg_user_from_request(request):
    init_data = ""
    if request.method == "GET":
        init_data = request.GET.get("initData", "")
    elif request.method == "POST":
        if request.content_type == "application/json":
            try:
                data = json.loads(request.body.decode('utf-8'))
                init_data = data.get("initData", "")
            except Exception:
                pass
        else:
            init_data = request.POST.get("initData", "")
    
    user_data = verify_telegram_web_app_data(init_data)
    telegram_id = user_data["id"] if user_data and "id" in user_data else 123456789
    return telegram_id, user_data

def get_or_create_django_user(telegram_id, user_data=None):
    user = User.objects.filter(telegram_id=telegram_id).first()
    if not user:
        first_name = user_data.get("first_name") if user_data else "Foydalanuvchi"
        last_name = user_data.get("last_name") if user_data else ""
        username = user_data.get("username") if user_data else None
        photo_url = user_data.get("photo_url") if user_data else None
        
        full_name = f"{first_name or ''} {last_name or ''}".strip()
        user = User.objects.create(
            telegram_id=telegram_id,
            username=username,
            name=full_name or "Foydalanuvchi",
            first_name=first_name,
            last_name=last_name,
            phone_number=f"ID: {telegram_id}",
            photo_url=photo_url,
            daily_goal_kcal=2000.0,
            streak_days=1,
            points=100,
            level=1
        )
    else:
        # Update missing fields if available
        if user_data:
            if user_data.get("first_name") and not user.first_name:
                user.first_name = user_data.get("first_name")
            if user_data.get("last_name") and not user.last_name:
                user.last_name = user_data.get("last_name")
            if user_data.get("username") and not user.username:
                user.username = user_data.get("username")
            if user_data.get("photo_url") and not user.photo_url:
                user.photo_url = user_data.get("photo_url")
            
            full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
            if full_name and user.name != full_name:
                user.name = full_name
            user.save()
    return user

@csrf_exempt
@require_http_methods(["GET"])
def api_dashboard(request):
    telegram_id, user_data = get_tg_user_from_request(request)
    user = get_or_create_django_user(telegram_id, user_data)
    
    today = date.today()
    today_meals = Meal.objects.filter(user=user, created_at__date=today).order_by('-created_at')
    
    total_calories = sum(m.calories for m in today_meals)
    total_protein = sum(m.protein_g for m in today_meals)
    total_fat = sum(m.fat_g for m in today_meals)
    total_carbs = sum(m.carbs_g for m in today_meals)
    
    remaining_calories = max(0.0, user.daily_goal_kcal - total_calories)
    progress_percent = min(100.0, round((total_calories / user.daily_goal_kcal * 100.0), 1)) if user.daily_goal_kcal > 0 else 0.0
    
    # Weekly stats for current week (Mon to Sun)
    start_of_week = today - timedelta(days=today.weekday())
    day_names = ['Dush', 'Sesh', 'Chor', 'Pay', 'Jum', 'Shan', 'Yak']
    weekly_stats = []
    
    for i in range(7):
        current_day = start_of_week + timedelta(days=i)
        day_meals = Meal.objects.filter(user=user, created_at__date=current_day)
        day_cal = sum(m.calories for m in day_meals)
        weekly_stats.append({
            "day": day_names[i],
            "date": current_day.strftime("%Y-%m-%d"),
            "calories": round(day_cal)
        })
        
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
        
    badges = list(Achievement.objects.filter(user=user).values_list('badge_code', flat=True))
    
    display_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.name or user.username or "Foydalanuvchi"
    contact_info = user.phone_number if (user.phone_number and "8817446491" not in user.phone_number) else f"ID: {user.telegram_id}"
    
    return JsonResponse({
        "status": "success",
        "user": {
            "telegram_id": user.telegram_id,
            "name": display_name,
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "username": user.username or "",
            "phone_number": contact_info,
            "photo_url": user.photo_url or "",
            "contact_info": contact_info,
            "dob": user.dob or "2000-01-01",
            "daily_goal_kcal": user.daily_goal_kcal,
            "is_vip": user.is_vip,
            "streak_days": user.streak_days,
            "points": user.points,
            "level": user.level,
            "weight_kg": user.weight_kg,
            "target_weight_kg": user.target_weight_kg,
            "height_cm": user.height_cm,
            "age": user.age,
            "gender": user.gender or "Male",
            "activity_level": user.activity_level,
            "diet_preference": user.diet_preference
        },
        "today_stats": {
            "total_calories": round(total_calories),
            "total_protein": round(total_protein, 1),
            "total_fat": round(total_fat, 1),
            "total_carbs": round(total_carbs, 1),
            "remaining_calories": round(remaining_calories),
            "progress_percent": progress_percent
        },
        "weekly_stats": weekly_stats,
        "today_meals": meals_list,
        "badges": badges
    })

@csrf_exempt
@require_http_methods(["POST"])
def api_profile(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = {}
        
    init_data = data.get("initData", "")
    user_data = verify_telegram_web_app_data(init_data)
    telegram_id = user_data["id"] if user_data and "id" in user_data else 123456789
    
    user = get_or_create_django_user(telegram_id, user_data)
    
    if data.get("name"):
        user.name = data["name"]
        parts = data["name"].split(" ", 1)
        user.first_name = parts[0]
        if len(parts) > 1:
            user.last_name = parts[1]
    if data.get("phone_number"):
        user.phone_number = data["phone_number"]
    if data.get("dob"):
        user.dob = data["dob"]
    if data.get("gender"):
        user.gender = data["gender"]
    if data.get("height_cm"):
        user.height_cm = float(data["height_cm"])
    if data.get("weight_kg"):
        user.weight_kg = float(data["weight_kg"])
    if data.get("target_weight_kg"):
        user.target_weight_kg = float(data["target_weight_kg"])
    if data.get("daily_goal_kcal"):
        user.daily_goal_kcal = float(data["daily_goal_kcal"])
    if data.get("activity_level"):
        user.activity_level = data["activity_level"]
    if data.get("diet_preference"):
        user.diet_preference = data["diet_preference"]
        
    user.save()
    
    display_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.name or "Foydalanuvchi"
    return JsonResponse({
        "status": "success",
        "user": {
            "telegram_id": user.telegram_id,
            "name": display_name,
            "phone_number": user.phone_number,
            "gender": user.gender,
            "height_cm": user.height_cm,
            "weight_kg": user.weight_kg,
            "daily_goal_kcal": user.daily_goal_kcal
        }
    })

@csrf_exempt
@require_http_methods(["POST"])
def api_scan_photo(request):
    init_data = request.POST.get("initData", "")
    user_data = verify_telegram_web_app_data(init_data)
    telegram_id = user_data["id"] if user_data and "id" in user_data else 123456789
    
    user = get_or_create_django_user(telegram_id, user_data)
    file_obj = request.FILES.get("file")
    if not file_obj:
        return JsonResponse({"status": "error", "error": "Rasm fayli yuklanmadi"}, status=400)
        
    image_bytes = file_obj.read()
    
    # Run async AIService analyzer in event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        parsed_data = loop.run_until_complete(AIService.analyze_food_image(image_bytes, is_vip=user.is_vip))
    finally:
        loop.close()
        
    return JsonResponse({
        "status": "success",
        "data": parsed_data,
        "remaining": 99
    })

@csrf_exempt
@require_http_methods(["POST"])
def api_scan_text(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = {}
        
    init_data = data.get("initData", "")
    text = data.get("text", "")
    user_data = verify_telegram_web_app_data(init_data)
    telegram_id = user_data["id"] if user_data and "id" in user_data else 123456789
    
    user = get_or_create_django_user(telegram_id, user_data)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        parsed_data = loop.run_until_complete(AIService.analyze_food_text(text, is_vip=user.is_vip))
    finally:
        loop.close()
        
    return JsonResponse({
        "status": "success",
        "data": parsed_data,
        "remaining": 99
    })

@csrf_exempt
@require_http_methods(["POST"])
def api_save_meal(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = {}
        
    init_data = data.get("initData", "")
    user_data = verify_telegram_web_app_data(init_data)
    telegram_id = user_data["id"] if user_data and "id" in user_data else 123456789
    
    user = get_or_create_django_user(telegram_id, user_data)
    
    meal = Meal.objects.create(
        user=user,
        food_name=data.get("food_name", "Taom"),
        weight_g=float(data.get("weight_g", 150)),
        calories=float(data.get("calories", 0)),
        protein_g=float(data.get("protein_g", 0)),
        fat_g=float(data.get("fat_g", 0)),
        carbs_g=float(data.get("carbs_g", 0)),
        meal_time=data.get("meal_time", "snack")
    )
    
    today = date.today()
    today_meals = Meal.objects.filter(user=user, created_at__date=today)
    total_calories = sum(m.calories for m in today_meals)
    
    return JsonResponse({
        "status": "success",
        "meal_id": meal.id,
        "streak_days": user.streak_days,
        "today_stats": {
            "total_calories": round(total_calories)
        }
    })

@csrf_exempt
@require_http_methods(["POST"])
def api_goals(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = {}
        
    init_data = data.get("initData", "")
    user_data = verify_telegram_web_app_data(init_data)
    telegram_id = user_data["id"] if user_data and "id" in user_data else 123456789
    
    user = get_or_create_django_user(telegram_id, user_data)
    
    if data.get("daily_goal_kcal"):
        user.daily_goal_kcal = float(data["daily_goal_kcal"])
    if data.get("weight_kg"):
        user.weight_kg = float(data["weight_kg"])
    user.save()
    
    return JsonResponse({
        "status": "success",
        "daily_goal_kcal": user.daily_goal_kcal,
        "weight_kg": user.weight_kg
    })

@csrf_exempt
@require_http_methods(["POST"])
def api_reset_user(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = {}
        
    init_data = data.get("initData", "")
    user_data = verify_telegram_web_app_data(init_data)
    telegram_id = user_data["id"] if user_data and "id" in user_data else 123456789
    
    user = User.objects.filter(telegram_id=telegram_id).first()
    if user:
        # Delete user's meals and achievements
        Meal.objects.filter(user=user).delete()
        Achievement.objects.filter(user=user).delete()
        Reminder.objects.filter(user=user).delete()
        
        # Reset metrics to default onboarding state
        user.streak_days = 0
        user.points = 0
        user.daily_goal_kcal = 2000.0
        user.weight_kg = 70.0
        user.target_weight_kg = 65.0
        user.height_cm = 170.0
        user.save()
        
    return JsonResponse({"status": "success", "message": "User reset successfully"})

@csrf_exempt
@require_http_methods(["GET"])
def api_diets(request):
    try:
        from .models import DietPlan
        diets = DietPlan.objects.filter(is_active=True).order_by('id')
        diet_list = []
        for d in diets:
            diet_list.append({
                "id": d.slug,
                "title": d.title,
                "description": d.description,
                "calories": round(d.calories),
                "protein": round(d.protein_g),
                "carbs": round(d.carbs_g),
                "fat": round(d.fat_g),
                "goal": d.goal,
                "image": d.image_url,
                "isMyDiet": d.is_my_diet
            })
        return JsonResponse({"status": "success", "diets": diet_list})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def api_submit_receipt(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = {}
        
    init_data = data.get("initData", "")
    plan_type = data.get("plan_type", "monthly")
    amount_som = data.get("amount_som", 29000)
    receipt_b64 = data.get("receipt_b64", "")
    
    user_data = verify_telegram_web_app_data(init_data)
    telegram_id = user_data["id"] if user_data and "id" in user_data else 123456789
    
    user = get_or_create_django_user(telegram_id, user_data)
    
    import base64
    from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
    from config import settings
    from bot import bot
    
    plan_label = "Oylik Premium (29,000 so'm)" if plan_type == "monthly" else "Yillik Premium (299,000 so'm)"
    
    admin_msg = (
        f"💳 **YANGI PREMIUM TO'LOV CHEKI KELDI!**\n\n"
        f"👤 **Foydalanuvchi:** {user.name or user.first_name} (`{user.telegram_id}`)\n"
        f"📞 **Aloqa:** {user.phone_number or 'Mavjud emas'}\n"
        f"📦 **Rejim:** {plan_label}\n"
        f"💰 **Summa:** {amount_som:,} so'm\n"
        f"⏰ **Vaqt:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"Quyidagi tugmalar orqali tasdiqlang yoki rad eting:"
    )
    
    approve_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ VIP Berish", callback_data=f"approve_vip_{user.telegram_id}_{plan_type}"),
                InlineKeyboardButton(text="❌ Rad Etish", callback_data=f"reject_vip_{user.telegram_id}")
            ]
        ]
    )
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        if receipt_b64 and "," in receipt_b64:
            header, img_str = receipt_b64.split(",", 1)
            img_data = base64.b64decode(img_str)
            photo_file = BufferedInputFile(img_data, filename=f"receipt_{user.telegram_id}.jpg")
            loop.run_until_complete(
                bot.send_photo(
                    chat_id=7225597812,
                    photo=photo_file,
                    caption=admin_msg,
                    parse_mode="Markdown",
                    reply_markup=approve_kb
                )
            )
        else:
            loop.run_until_complete(
                bot.send_message(
                    chat_id=7225597812,
                    text=admin_msg,
                    parse_mode="Markdown",
                    reply_markup=approve_kb
                )
            )
    except Exception as e:
        print("Admin notification error:", e)
    finally:
        loop.close()

    return JsonResponse({
        "status": "success",
        "message": "To'lov cheki adminga muvaffaqiyatli yuborildi!"
    })
