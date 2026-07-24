"""
Configuracion de Django para el Back Office de la Mini App Toka.
Las credenciales sensibles se leen desde el archivo .env (python-decouple).
"""
from datetime import timedelta
from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------
# Seguridad
# ------------------------------------------------------------------
SECRET_KEY = config("SECRET_KEY", default="unsafe-dev-key")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())

# ------------------------------------------------------------------
# Aplicaciones
# ------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.users",
    "apps.catalog",
    "apps.inventory",
    "apps.orders",
    "apps.payments",
    "apps.ads",
    "apps.reverse_logistics",
    "apps.reports",
    "apps.toka",
    "apps.public_api",
    "apps.miniapp",
    "apps.locations",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise sirve los archivos estaticos en produccion (justo tras Security).
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ------------------------------------------------------------------
# Base de datos - PostgreSQL (credenciales en .env)
# ------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="backoffice_toka"),
        "USER": config("DB_USER", default="postgres"),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default="127.0.0.1"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

# SSL para bases gestionadas (ej. Render). Vacio en local.
_db_sslmode = config("DB_SSLMODE", default="")
if _db_sslmode:
    DATABASES["default"]["OPTIONS"] = {"sslmode": _db_sslmode}

# ------------------------------------------------------------------
# Autenticacion / Usuario personalizado
# ------------------------------------------------------------------
AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------------------------------------
# Internacionalizacion
# ------------------------------------------------------------------
LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------
# Archivos estaticos y media (imagenes de Ads / carrusel)
# ------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# WhiteNoise: comprime y cachea los estaticos servidos en produccion.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# ------------------------------------------------------------------
# Almacenamiento de imagenes en Cloudflare R2 (S3-compatible)
# ------------------------------------------------------------------
# Cuando USE_R2=True, las imagenes cargadas desde el back office (banners,
# iconos de categorias, logos de marcas e imagenes de productos) se suben a R2
# y sus .url apuntan al dominio publico -> Wigilabs las consume sin URLs rotas.
USE_R2 = config("USE_R2", default=False, cast=bool)
if USE_R2:
    R2_ACCOUNT_ID = config("R2_ACCOUNT_ID")
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": config("R2_BUCKET"),
            "endpoint_url": f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            "access_key": config("R2_ACCESS_KEY_ID"),
            "secret_key": config("R2_SECRET_ACCESS_KEY"),
            # Dominio publico del bucket (pub-xxxx.r2.dev), sin https://.
            "custom_domain": config("R2_PUBLIC_DOMAIN"),
            "region_name": "auto",
            "signature_version": "s3v4",
            # R2 no usa ACLs y servimos via URL publica -> URLs limpias sin firma.
            "default_acl": None,
            "querystring_auth": False,
            # No sobrescribir: si suben dos archivos con el mismo nombre, renombra.
            "file_overwrite": False,
        },
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ------------------------------------------------------------------
# Django REST Framework
# ------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        # Permite que el staff logueado en /admin/ vea la documentacion Swagger.
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Rate por defecto para la API publica; se ajusta por consumidor
    # (rate_limit_per_min de cada ApiClient) en ApiClientRateThrottle.
    "DEFAULT_THROTTLE_RATES": {
        "public_api": "60/min",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=config("ACCESS_TOKEN_LIFETIME_MIN", default=60, cast=int)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=config("REFRESH_TOKEN_LIFETIME_DAYS", default=7, cast=int)
    ),
    "ROTATE_REFRESH_TOKENS": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Back Office Mini App Toka - API",
    "DESCRIPTION": "APIs del back office para la mini app (pedidos, pagos, catalogo, inventario).",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # La documentacion (schema y Swagger) solo es visible para usuarios
    # autenticados; nadie sin login puede ver la estructura de la API.
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAuthenticated"],
}

# ------------------------------------------------------------------
# CORS (frontend React)
# ------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:5173,http://127.0.0.1:5173",
    cast=Csv(),
)

# ------------------------------------------------------------------
# Produccion / detras de proxy (Render termina el TLS y reenvia)
# ------------------------------------------------------------------
# Dominios de confianza para POST con CSRF (ej. login del /admin/ por HTTPS).
# DEBE incluir el esquema: https://tu-servicio.onrender.com
CSRF_TRUSTED_ORIGINS = [
    o for o in config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv()) if o
]

if not DEBUG:
    # Render entrega el request por HTTP interno con esta cabecera puesta a https.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# ------------------------------------------------------------------
# Integracion Super App TOKA
# ------------------------------------------------------------------
TOKA_ENV = config("TOKA_ENV", default="UAT")
TOKA_API_BASE_URL = config("TOKA_API_BASE_URL", default="")
# Verificacion TLS. En UAT (cert self-signed / proxy corporativo) puede ser False.
# En PRODUCCION debe ser True. Si tienes el CA corporativo, mejor usa TOKA_CA_BUNDLE.
TOKA_VERIFY_SSL = config("TOKA_VERIFY_SSL", default=True, cast=bool)
TOKA_CA_BUNDLE = config("TOKA_CA_BUNDLE", default="")
TOKA_CLIENT_ID = config("TOKA_CLIENT_ID", default="")
TOKA_MERCHANT_ID = config("TOKA_MERCHANT_ID", default="")
TOKA_APP_ID = config("TOKA_APP_ID", default="")

# Rutas a las llaves RSA (.pem)
TOKA_PRIVATE_KEY_PATH = config("TOKA_PRIVATE_KEY_PATH", default="")
TOKA_PUBLIC_KEY_PATH = config("TOKA_PUBLIC_KEY_PATH", default="")
TOKA_TOKA_PUBLIC_KEY_PATH = config("TOKA_TOKA_PUBLIC_KEY_PATH", default="")

# Pago (Mini Program Payment) - Fase 4.
# URL a la que Toka notifica el resultado del pago (nuestro webhook servidor-a-
# servidor). Redirect es a donde vuelve el usuario tras el checkout.
TOKA_PAYMENT_NOTIFY_URL = config("TOKA_PAYMENT_NOTIFY_URL", default="")
TOKA_PAYMENT_REDIRECT_URL = config("TOKA_PAYMENT_REDIRECT_URL", default="")

# Legado (esquema anterior; ya no se usa con firma RSA)
TOKA_API_KEY = config("TOKA_API_KEY", default="")
TOKA_WEBHOOK_SECRET = config("TOKA_WEBHOOK_SECRET", default="")

# ------------------------------------------------------------------
# BFF de la mini-app (Wigilabs / Supli) - API /v1
# ------------------------------------------------------------------
# Duracion del sessionToken PROPIO de Supli (NO el de Toka). Configurable.
MINIAPP_SESSION_TTL_MIN = config(
    "SESSION_TOKEN_LIFETIME_MIN", default=60, cast=int
)
# Si True, el catalogo/contenido/ubicaciones son publicos (como propone Wigilabs).
# Si False (por defecto), TODOS los endpoints /v1 exigen Bearer sessionToken,
# salvo auth/session (que emite el token).
MINIAPP_PUBLIC_CATALOG = config("MINIAPP_PUBLIC_CATALOG", default=False, cast=bool)
