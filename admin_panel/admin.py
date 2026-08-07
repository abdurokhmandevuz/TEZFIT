from django.contrib import admin
from django.utils.html import format_html
from .models import User, Meal, Achievement, Reminder, DietPlan

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'telegram_id',
        'avatar_preview',
        'name',
        'phone_number',
        'is_vip',
        'daily_goal_kcal',
        'weight_kg',
        'height_cm',
        'streak_days',
        'points',
        'created_at'
    )
    list_filter = ('is_vip', 'gender', 'activity_level', 'diet_preference', 'created_at')
    search_fields = ('telegram_id', 'username', 'name', 'phone_number', 'first_name', 'last_name')
    list_editable = ('is_vip', 'daily_goal_kcal')
    ordering = ('-id',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ("Foydalanuvchi Ma'lumotlari", {
            'fields': ('telegram_id', 'username', 'name', 'first_name', 'last_name', 'phone_number', 'photo_url', 'dob')
        }),
        ("Salomatlik va Maqsadlar", {
            'fields': ('gender', 'age', 'height_cm', 'weight_kg', 'target_weight_kg', 'activity_level', 'diet_preference', 'daily_goal_kcal')
        }),
        ("Status va Gamifikatsiya", {
            'fields': ('is_vip', 'streak_days', 'points', 'level', 'free_requests_today', 'last_request_date', 'last_streak_date', 'created_at')
        }),
    )

    def avatar_preview(self, obj):
        if obj.photo_url:
            return format_html('<img src="{}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;" />', obj.photo_url)
        name_initial = (obj.name or "F")[0].upper()
        return format_html('<div style="width:36px;height:36px;border-radius:50%;background:#ff6b4a;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:bold;">{}</div>', name_initial)
    avatar_preview.short_description = "Rasm"

@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ('id', 'food_name', 'calories_badge', 'protein_g', 'fat_g', 'carbs_g', 'weight_g', 'user', 'created_at')
    list_filter = ('meal_time', 'created_at')
    search_fields = ('food_name', 'user__name', 'user__telegram_id', 'user__username')
    ordering = ('-created_at',)

    def calories_badge(self, obj):
        return format_html('<span style="color:#ff6b4a;font-weight:bold;">🔥 {} kcal</span>', round(obj.calories))
    calories_badge.short_description = "Kaloriya"

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('id', 'badge_code', 'user', 'earned_at')
    list_filter = ('badge_code', 'earned_at')
    search_fields = ('badge_code', 'user__name', 'user__telegram_id')

@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'reminder_type', 'reminder_time', 'is_active')
    list_filter = ('is_active', 'reminder_type')
    search_fields = ('user__name', 'user__telegram_id')
    list_editable = ('is_active', 'reminder_time')

@admin.register(DietPlan)
class DietPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'image_preview', 'title', 'slug', 'calories', 'protein_g', 'carbs_g', 'fat_g', 'is_my_diet', 'is_active')
    list_filter = ('is_active', 'is_my_diet')
    search_fields = ('title', 'slug', 'description', 'goal')
    list_editable = ('is_active', 'is_my_diet', 'calories')
    ordering = ('id',)

    def image_preview(self, obj):
        if obj.image_url:
            return format_html('<img src="{}" style="width:50px;height:36px;border-radius:8px;object-fit:cover;" />', obj.image_url)
        return "—"
    image_preview.short_description = "Rasm"

    def calories_badge(self, obj):
        return format_html('<span style="color:#ff6b4a;font-weight:bold;">🔥 {} kcal</span>', round(obj.calories))
    calories_badge.short_description = "Kaloriya"
