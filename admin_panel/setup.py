import sys
from django.core.management import call_command
from django.contrib.auth import get_user_model

def ensure_superuser():
    try:
        print("[Django Admin] Running database migrations...")
        call_command('migrate', interactive=False, verbosity=0)

        print("[Django Admin] Collecting static files for Jazzmin...")
        call_command('collectstatic', interactive=False, verbosity=0)

        User = get_user_model()
        username = "admin"
        email = "admin@gmail.com"
        password = "admin"

        # Force clean re-creation of superuser
        User.objects.filter(username=username).delete()

        admin_user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            is_staff=True,
            is_superuser=True,
            is_active=True
        )
        print(f"[Django Admin] Created superuser '{username}' (active={admin_user.is_active}, staff={admin_user.is_staff}) successfully!")

        ensure_default_diet_plans()
    except Exception as e:
        print(f"[Django Admin] Superuser Setup Error: {e}", file=sys.stderr)

def ensure_default_diet_plans():
    try:
        from admin_panel.models import DietPlan
        DEFAULT_DIETS = [
            {
                "slug": "mediterranean",
                "title": "O'rta Yer Dengizi Parhezi",
                "description": "Ushbu rejim tabiiy va to'liq mahsulotlarga yo'naltirilgan bo'lib, yangi sabzavotlar, sifatli zaytun yog'i, yog'siz baliq, yong'oqlar va foydali don mahsulotlarini o'z ichiga oladi.",
                "calories": 2000.0,
                "protein_g": 120.0,
                "carbs_g": 200.0,
                "fat_g": 70.0,
                "goal": "Yurak Salomatligi, Vaznni Saqlash",
                "image_url": "assets/diet_mediterranean.jpg",
                "is_active": True,
                "is_my_diet": False
            },
            {
                "slug": "lowcarb",
                "title": "Past Uglevodli Yog' Erituvchi",
                "description": "Tana yog' almashinuvini jadallashtirish uchun uglevodlarni cheklab, foydali yog'lar, avokado va oqsillarga asoslangan rejim.",
                "calories": 1800.0,
                "protein_g": 160.0,
                "carbs_g": 100.0,
                "fat_g": 80.0,
                "goal": "Tezkor Yog' Yo'qotish, Insulinga Sezgirlik",
                "image_url": "assets/diet_lowcarb.jpg",
                "is_active": True,
                "is_my_diet": True
            },
            {
                "slug": "vegan",
                "title": "Vegalarning Quvvat Rejasi",
                "description": "100% o'simlikka asoslangan, dukkakli ekinlar, dimlangan brokkoli, kinoa va foydali urug'lar bilan boyitilgan to'yimli diet.",
                "calories": 2000.0,
                "protein_g": 125.0,
                "carbs_g": 300.0,
                "fat_g": 55.0,
                "goal": "Toza Energiya, Hujayraviy Yangilanish",
                "image_url": "assets/diet_vegan.jpg",
                "is_active": True,
                "is_my_diet": True
            }
        ]

        for d in DEFAULT_DIETS:
            DietPlan.objects.get_or_create(slug=d["slug"], defaults=d)
        print("[Django Admin] Default Diet Plans populated successfully!")
    except Exception as e:
        print(f"[Django Admin] DietPlan Initial Setup Error: {e}", file=sys.stderr)
