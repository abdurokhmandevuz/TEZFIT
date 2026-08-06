from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Meal, User

class MealService:
    @staticmethod
    async def add_meal(
        session: AsyncSession,
        user_id: int,
        food_name: str,
        weight_g: float,
        calories: float,
        protein_g: float,
        fat_g: float,
        carbs_g: float,
        meal_time: str = "snack",
        photo_file_id: Optional[str] = None
    ) -> Meal:
        meal = Meal(
            user_id=user_id,
            food_name=food_name,
            weight_g=weight_g,
            calories=calories,
            protein_g=protein_g,
            fat_g=fat_g,
            carbs_g=carbs_g,
            meal_time=meal_time,
            photo_file_id=photo_file_id,
            created_at=datetime.utcnow()
        )
        session.add(meal)
        await session.commit()
        await session.refresh(meal)
        return meal

    @staticmethod
    async def get_today_stats(session: AsyncSession, user_id: int) -> Dict[str, float]:
        """Get sum of calories and macros for today."""
        today_start = datetime.combine(date.today(), datetime.min.time())
        stmt = select(
            func.coalesce(func.sum(Meal.calories), 0.0).label("total_calories"),
            func.coalesce(func.sum(Meal.protein_g), 0.0).label("total_protein"),
            func.coalesce(func.sum(Meal.fat_g), 0.0).label("total_fat"),
            func.coalesce(func.sum(Meal.carbs_g), 0.0).label("total_carbs"),
            func.count(Meal.id).label("meal_count")
        ).where(
            and_(Meal.user_id == user_id, Meal.created_at >= today_start)
        )
        result = await session.execute(stmt)
        row = result.one()
        return {
            "total_calories": float(row.total_calories),
            "total_protein": float(row.total_protein),
            "total_fat": float(row.total_fat),
            "total_carbs": float(row.total_carbs),
            "meal_count": int(row.meal_count)
        }

    @staticmethod
    async def get_today_meals(session: AsyncSession, user_id: int) -> List[Meal]:
        today_start = datetime.combine(date.today(), datetime.min.time())
        stmt = select(Meal).where(
            and_(Meal.user_id == user_id, Meal.created_at >= today_start)
        ).order_by(Meal.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_weekly_stats(session: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        """Get daily calorie sum for the last 7 days."""
        seven_days_ago = datetime.combine(date.today() - timedelta(days=6), datetime.min.time())
        stmt = select(Meal).where(
            and_(Meal.user_id == user_id, Meal.created_at >= seven_days_ago)
        ).order_by(Meal.created_at.asc())
        result = await session.execute(stmt)
        meals = result.scalars().all()

        daily_data = {}
        for i in range(7):
            day_dt = date.today() - timedelta(days=6 - i)
            day_str = day_dt.strftime("%Y-%m-%d")
            daily_data[day_str] = {"date": day_str, "calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}

        for meal in meals:
            day_str = meal.created_at.strftime("%Y-%m-%d")
            if day_str in daily_data:
                daily_data[day_str]["calories"] += meal.calories
                daily_data[day_str]["protein"] += meal.protein_g
                daily_data[day_str]["fat"] += meal.fat_g
                daily_data[day_str]["carbs"] += meal.carbs_g

        return list(daily_data.values())
