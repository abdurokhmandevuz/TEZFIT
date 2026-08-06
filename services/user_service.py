from datetime import date
from typing import Tuple, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from config import settings

class UserService:
    @staticmethod
    async def get_or_create_user(session: AsyncSession, telegram_id: int, username: Optional[str] = None, name: Optional[str] = None) -> User:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        today = date.today()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                name=name,
                free_requests_today=0,
                last_request_date=today,
                daily_goal_kcal=2000.0
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            # Check if date changed to reset daily free counter
            if user.last_request_date != today:
                user.free_requests_today = 0
                user.last_request_date = today
                await session.commit()
                await session.refresh(user)
        return user

    @staticmethod
    async def check_and_increment_limit(session: AsyncSession, user: User) -> Tuple[bool, int]:
        """
        Check whether user has request quota left today.
        Returns (is_allowed, remaining_requests).
        VIP users have unlimited requests (-1).
        """
        if user.is_vip:
            return True, -1
        
        today = date.today()
        if user.last_request_date != today:
            user.free_requests_today = 0
            user.last_request_date = today

        if user.free_requests_today >= settings.USER_FREE_DAILY_LIMIT:
            remaining = 0
            return False, remaining

        user.free_requests_today += 1
        await session.commit()
        remaining = settings.USER_FREE_DAILY_LIMIT - user.free_requests_today
        return True, remaining

    @staticmethod
    def calculate_mifflin_st_jeor(weight_kg: float, height_cm: float, age: int, gender: str = "male") -> float:
        """
        Calculates daily calorie goal using Mifflin-St Jeor formula.
        BMR = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + (5 if male else -161)
        TDEE = BMR * 1.375 (moderate activity multiplier)
        """
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
        if gender.lower() == "female" or gender.lower() == "ayol":
            bmr -= 161
        else:
            bmr += 5
        
        tdee = bmr * 1.375
        return round(tdee, 1)

    @staticmethod
    async def update_profile(
        session: AsyncSession,
        user: User,
        weight_kg: Optional[float] = None,
        height_cm: Optional[float] = None,
        age: Optional[int] = None,
        gender: Optional[str] = None,
        daily_goal_kcal: Optional[float] = None
    ) -> User:
        if weight_kg is not None:
            user.weight_kg = weight_kg
        if height_cm is not None:
            user.height_cm = height_cm
        if age is not None:
            user.age = age
        if gender is not None:
            user.gender = gender
        
        if daily_goal_kcal is not None:
            user.daily_goal_kcal = daily_goal_kcal
        elif weight_kg or height_cm or age or gender:
            w = user.weight_kg or 70.0
            h = user.height_cm or 170.0
            a = user.age or 25
            g = user.gender or "male"
            user.daily_goal_kcal = UserService.calculate_mifflin_st_jeor(w, h, a, g)

        await session.commit()
        await session.refresh(user)
        return user
