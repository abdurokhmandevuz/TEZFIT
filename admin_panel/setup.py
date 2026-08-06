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

        # Re-create admin user to ensure clean password hashing
        user = User.objects.filter(username=username).first()
        if user:
            user.set_password(password)
            user.email = email
            user.is_superuser = True
            user.is_staff = True
            user.is_active = True
            user.save()
            print(f"[Django Admin] Superuser '{username}' password successfully updated to 'admin'!")
        else:
            print(f"[Django Admin] Creating superuser '{username}'...")
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                is_staff=True,
                is_superuser=True,
                is_active=True
            )
            print("[Django Admin] Superuser 'admin' created successfully with password 'admin'!")
    except Exception as e:
        print(f"[Django Admin] Setup Error: {e}", file=sys.stderr)
