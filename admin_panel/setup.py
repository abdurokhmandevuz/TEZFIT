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
    except Exception as e:
        print(f"[Django Admin] Superuser Setup Error: {e}", file=sys.stderr)
