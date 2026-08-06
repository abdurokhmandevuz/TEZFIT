import os
import sys
import logging
from pathlib import Path
from config import settings as app_settings

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-tezfit-admin-key-secret-super-safe'
DEBUG = True
ALLOWED_HOSTS = ['*']

LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/admin/login/'

# CSRF & Proxy Configuration for Railway HTTPS
CSRF_TRUSTED_ORIGINS = [
    'https://*.railway.app',
    'https://*.up.railway.app',
    'https://tezfit-production.up.railway.app',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://0.0.0.0:8000',
]
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'admin_panel',
]

class ExceptionLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        import traceback
        print("========== DJANGO EXCEPTION TRACEBACK ==========", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("================================================", file=sys.stderr)
        return None

MIDDLEWARE = [
    'admin_panel.settings.ExceptionLoggingMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'admin_panel.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'admin_panel.wsgi.application'

# Database Configuration (pointing to SQLite / Postgres)
db_url = app_settings.DATABASE_URL
if "sqlite" in db_url:
    db_path = db_url.split(":///")[-1]
    if not os.path.isabs(db_path) and not db_path.startswith("./"):
        db_path = f"./{db_path}"
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': db_path,
            'OPTIONS': {
                'timeout': 20,
            }
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'kalorix.db',
            'OPTIONS': {
                'timeout': 20,
            }
        }
    }

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'uz-uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/admin_static/'
STATIC_ROOT = BASE_DIR / 'static_collected'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==================== JAZZMIN ADMIN CONFIGURATION ====================
JAZZMIN_SETTINGS = {
    "site_title": "TezFIT Admin",
    "site_header": "TezFIT Boshqaruv Paneli",
    "site_brand": "TezFIT AI",
    "site_icon": None,
    "welcome_sign": "TezFIT Boshqaruv Paneliga Xush Kelibsiz! 👋",
    "copyright": "TezFIT Dev Team",
    "search_model": "admin_panel.User",
    "user_avatar": None,
    "topmenu_links": [
        {"name": "Bosh Sahifa", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Web App", "url": "/web_app", "new_window": True},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "admin_panel.User": "fas fa-users",
        "admin_panel.Meal": "fas fa-utensils",
        "admin_panel.Achievement": "fas fa-award",
        "admin_panel.Reminder": "fas fa-bell",
        "auth.Group": "fas fa-users-cog",
        "auth.User": "fas fa-user-shield",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": True,
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_booster": True,
    "changeform_format": "horizontal_tabs",
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-primary",
    "navbar": "navbar-dark navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-warning",
    "sidebar_nav_small_text": False,
    "theme": "darkly",
    "dark_mode_theme": "darkly",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}
