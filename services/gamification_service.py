from datetime import date, timedelta
from typing import List, Dict, Any, Tuple
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Meal, Achievement

BADGES = {
    "FIRST_MEAL": {"name": "Birinchi qadam 🥗", "desc": "1-ovqat saqlandi"},
    "STREAK_7": {"name": "7 kunlik otash 🔥", "desc": "7 kun uzluksiz ovqatlar kiritildi"},
    "STREAK_30": {"name": "Afsonaviy intizom 🏆", "desc": "30 kunlik streak o'rnatildi"},
    "MEALS_50": {"name": "Gurman 50 🍲", "desc": "50 ta ovqat kiritildi"},
    "GOAL_REACHED": {"name": "Maqsad ustasi 🎯", "desc": "Kunlik kaloriya maqsadi bajarildi"}
}

class GamificationService:
    @staticmethod
    async def update_user_streak(session: AsyncSession, user: User) -> Tuple[int, bool]:
        """
        Updates streak count for user. Returns (current_streak, is_new_badge_earned).
        """
        today = date.today()
        yesterday = today - timedelta(days=1)

        if user.last_streak_date == today:
            return user.streak_days, False

        if user.last_streak_date == yesterday:
            user.streak_days += 1
        else:
            user.streak_days = 1

        user.last_streak_date = today
        await session.commit()
        await session.refresh(user)

        # Check badges for streak
        new_badge = False
        if user.streak_days >= 7:
            new_badge = await GamificationService.award_badge(session, user.id, "STREAK_7") or new_badge
        if user.streak_days >= 30:
            new_badge = await GamificationService.award_badge(session, user.id, "STREAK_30") or new_badge

        return user.streak_days, new_badge

    @staticmethod
    async def award_badge(session: AsyncSession, user_id: int, badge_code: str) -> bool:
        """Awards a badge if user doesn't already have it. Returns True if awarded."""
        stmt = select(Achievement).where(
            Achievement.user_id == user_id,
            Achievement.badge_code == badge_code
        )
        res = await session.execute(stmt)
        if res.scalar_one_or_none():
            return False

        achievement = Achievement(user_id=user_id, badge_code=badge_code)
        session.add(achievement)
        await session.commit()
        return True

    @staticmethod
    async def check_all_achievements(session: AsyncSession, user: User, total_today_calories: float) -> List[str]:
        """Check all possible achievements for user after logging a meal."""
        earned_now = []

        # 1. First meal badge
        stmt_count = select(func.count(Meal.id)).where(Meal.user_id == user.id)
        count_res = await session.execute(stmt_count)
        meal_count = count_res.scalar_one()

        if meal_count >= 1:
            if await GamificationService.award_badge(session, user.id, "FIRST_MEAL"):
                earned_now.append(BADGES["FIRST_MEAL"]["name"])

        if meal_count >= 50:
            if await GamificationService.award_badge(session, user.id, "MEALS_50"):
                earned_now.append(BADGES["MEALS_50"]["name"])

        # Goal reached check
        if total_today_calories >= (user.daily_goal_kcal * 0.9) and total_today_calories <= (user.daily_goal_kcal * 1.1):
            if await GamificationService.award_badge(session, user.id, "GOAL_REACHED"):
                earned_now.append(BADGES["GOAL_REACHED"]["name"])

        return earned_now

    @staticmethod
    async def get_leaderboard(session: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top users by streak_days."""
        stmt = select(User).order_by(desc(User.streak_days), desc(User.created_at)).limit(limit)
        res = await session.execute(stmt)
        users = res.scalars().all()

        board = []
        for rank, u in enumerate(users, start=1):
            display_name = u.name or u.username or f"Foydalanuvchi #{u.telegram_id % 10000}"
            board.append({
                "rank": rank,
                "name": display_name,
                "streak": u.streak_days,
                "is_vip": u.is_vip
            })
        return board

    @staticmethod
    async def get_user_badges(session: AsyncSession, user_id: int) -> List[Dict[str, str]]:
        stmt = select(Achievement).where(Achievement.user_id == user_id)
        res = await session.execute(stmt)
        achievements = res.scalars().all()
        
        result = []
        for ach in achievements:
            if ach.badge_code in BADGES:
                result.append({
                    "code": ach.badge_code,
                    "name": BADGES[ach.badge_code]["name"],
                    "desc": BADGES[ach.badge_code]["desc"],
                    "earned_at": ach.earned_at.strftime("%Y-%m-%d")
                })
        return result
