import sys
from django.core.management import call_command
from django.contrib.auth import get_user_model

def ensure_superuser():
    try:
        print("[Django Admin] Running database migrations...")
        call_command('migrate', interactive=False, verbosity=1)

        User = get_user_model()
        username = "admin"
        email = "admin@gmail.com"
        password = "admin"

        user = User.objects.filter(username=username).first()
        if not user:
            print(f"[Django Admin] Creating superuser '{username}' with email '{email}'...")
            User.objects.create_superuser(username=username, email=email, password=password)
            print("[Django Admin] Superuser created successfully! Login with admin / admin")
        else:
            user.set_password(password)
            user.email = email
            user.is_superuser = True
            user.is_staff = True
            user.save()
            print(f"[Django Admin] Superuser '{username}' updated with credentials admin / admin!")
    except Exception as e:
        print(f"[Django Admin] Migration / Superuser Error: {e}", file=sys.stderr)
        raise e
