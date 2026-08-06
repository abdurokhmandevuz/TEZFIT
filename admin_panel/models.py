from django.db import models

class User(models.Model):
    id = models.AutoField(primary_key=True)
    telegram_id = models.BigIntegerField(unique=True, db_index=True, verbose_name="Telegram ID")
    username = models.CharField(max_length=255, null=True, blank=True, verbose_name="Username")
    name = models.CharField(max_length=255, null=True, blank=True, verbose_name="To'liq Ismi")
    first_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="Ismi")
    last_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="Familiyasi")
    phone_number = models.CharField(max_length=100, null=True, blank=True, verbose_name="Telefon / ID")
    photo_url = models.CharField(max_length=512, null=True, blank=True, verbose_name="Rasm URL")
    dob = models.CharField(max_length=100, default="2000-01-01", verbose_name="Tug'ilgan sana")
    
    weight_kg = models.FloatField(default=70.0, null=True, blank=True, verbose_name="Vazn (kg)")
    target_weight_kg = models.FloatField(default=65.0, null=True, blank=True, verbose_name="Maqsadli vazn (kg)")
    height_cm = models.FloatField(default=170.0, null=True, blank=True, verbose_name="Bo'y (cm)")
    age = models.IntegerField(default=25, null=True, blank=True, verbose_name="Yosh")
    gender = models.CharField(max_length=50, default="Male", null=True, blank=True, verbose_name="Jinsi")
    activity_level = models.CharField(max_length=100, default="Lightly active", null=True, blank=True, verbose_name="Faollik")
    diet_preference = models.CharField(max_length=100, default="No preference", null=True, blank=True, verbose_name="Parhez afzalligi")
    
    daily_goal_kcal = models.FloatField(default=2000.0, verbose_name="Kunlik kaloriya normasi (kcal)")
    is_vip = models.BooleanField(default=False, verbose_name="VIP Status")
    streak_days = models.IntegerField(default=0, verbose_name="Streak kunlari")
    points = models.IntegerField(default=100, verbose_name="Ballar")
    level = models.IntegerField(default=1, verbose_name="Daraja")
    free_requests_today = models.IntegerField(default=0, verbose_name="Bugungi bepul so'rovlar")
    last_request_date = models.DateField(null=True, blank=True, verbose_name="Oxirgi so'rov sanasi")
    last_streak_date = models.DateField(null=True, blank=True, verbose_name="Oxirgi streak sanasi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ro'yxatdan o'tgan vaqti")

    class Meta:
        db_table = "users"
        managed = False
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "1. Foydalanuvchilar"

    def __str__(self):
        return f"{self.name or self.username or self.telegram_id} (ID: {self.telegram_id})"

class Meal(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", related_name="meals", verbose_name="Foydalanuvchi")
    photo_file_id = models.CharField(max_length=512, null=True, blank=True, verbose_name="Rasm File ID")
    food_name = models.CharField(max_length=255, verbose_name="Taom nomi")
    weight_g = models.FloatField(default=0.0, verbose_name="Vazn (g)")
    calories = models.FloatField(default=0.0, verbose_name="Kaloriya (kcal)")
    protein_g = models.FloatField(default=0.0, verbose_name="Oqsil (g)")
    fat_g = models.FloatField(default=0.0, verbose_name="Yog' (g)")
    carbs_g = models.FloatField(default=0.0, verbose_name="Uglevod (g)")
    meal_time = models.CharField(max_length=50, default="snack", verbose_name="Vaqt sektori")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Kiritilgan vaqti")

    class Meta:
        db_table = "meals"
        managed = False
        verbose_name = "Taom"
        verbose_name_plural = "2. Kiritilgan Taomlar"

    def __str__(self):
        return f"{self.food_name} ({self.calories} kcal) - {self.user}"

class Achievement(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", related_name="achievements", verbose_name="Foydalanuvchi")
    badge_code = models.CharField(max_length=100, verbose_name="Nishon kodi")
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name="Erishilgan vaqti")

    class Meta:
        db_table = "achievements"
        managed = False
        verbose_name = "Nishon/Yutuq"
        verbose_name_plural = "3. Foydalanuvchi Yutuqlari"

    def __str__(self):
        return f"{self.badge_code} - {self.user}"

class Reminder(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", related_name="reminders", verbose_name="Foydalanuvchi")
    reminder_time = models.CharField(max_length=10, default="08:00", verbose_name="Eslatish vaqti")
    reminder_type = models.CharField(max_length=50, default="breakfast", verbose_name="Eslatma turi")
    is_active = models.BooleanField(default=True, verbose_name="Faolmi")

    class Meta:
        db_table = "reminders"
        managed = False
        verbose_name = "Eslatma"
        verbose_name_plural = "4. Ovqatlanish Eslatmalari"

    def __str__(self):
        return f"{self.reminder_type} ({self.reminder_time}) - {self.user}"
