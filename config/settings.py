import os
from datetime import timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def _load_local_env() -> None:
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _env_bool(name: str, default: bool = False) -> bool:
    value = _env(name, str(default)).lower()
    return value in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    value = _env(name, str(default))
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _env_list(name: str, default: str = "") -> list[str]:
    raw = _env(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _database_config() -> dict:
    engine = _env("DB_ENGINE", "mssql")
    name = _env("DB_NAME", "cartillas_operaciones_mina")

    if engine == "sqlite":
        db_path = name if name else "db.sqlite3"
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(BASE_DIR / db_path),
        }

    config = {
        "ENGINE": engine,
        "NAME": name,
        "HOST": _env("DB_HOST", "localhost"),
        "PORT": _env("DB_PORT", "1433"),
        "USER": _env("DB_USER"),
        "PASSWORD": _env("DB_PASSWORD"),
    }

    driver = _env("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    if driver:
        config["OPTIONS"] = {"driver": driver}

    return config


_load_local_env()


SECRET_KEY = _env("SECRET_KEY", "dev-only-change-me")
DEBUG = _env_bool("DEBUG", False)
ALLOWED_HOSTS = _env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    # New managed apps for Cartillas Operaciones Mina.
    "core.apps.CoreConfig",
    "accounts.apps.AccountsConfig",
    "auth_api.apps.AuthApiConfig",
    "catalogos.apps.CatalogosConfig",
    "cartillas.apps.CartillasConfig",
    "mina.apps.MinaConfig",
    "sync.apps.SyncConfig",
    "attachments.apps.AttachmentsConfig",
    "reports.apps.ReportsConfig",
    # Legacy apps kept temporarily as reference while the new backend is built.
    "user.apps.UserConfig",
    "api",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if _env_bool("DEBUG_LOGIN_REQUESTS", False):
    MIDDLEWARE.insert(0, "api.views.middlewares.DebugLoginRequestMiddleware")


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


AUTH_USER_MODEL = "accounts.User"

DATABASES = {
    "default": _database_config(),
}

# Temporary compatibility alias for legacy services that still read this connection.
DATABASES["PORTAL_AEI"] = DATABASES["default"]


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=_env_int("JWT_ACCESS_MINUTES", 60),
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=_env_int("JWT_REFRESH_DAYS", 7)),
    "AUTH_HEADER_TYPES": ("Bearer",),
}


CORS_ALLOWED_ORIGINS = _env_list("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_ALL_ORIGINS = _env_bool("CORS_ALLOW_ALL_ORIGINS", False)


APIPERU_TOKEN = _env("APIPERU_TOKEN")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

STATIC_URL = "static/"

MEDIA_ROOT = BASE_DIR / _env("MEDIA_ROOT", "media")
MEDIA_URL = _env("MEDIA_URL", "/media/")


LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": str(LOGS_DIR / "backend_errors.log"),
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        "file_debug": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": str(LOGS_DIR / "backend_debug.log"),
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        "console": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file", "console"],
            "level": "ERROR",
        },
        "django.request": {
            "handlers": ["file", "console"],
            "level": "ERROR",
            "propagate": False,
        },
        "api": {
            "handlers": ["file", "console"],
            "level": "DEBUG" if DEBUG else "INFO",
        },
        "api.sync": {
            "handlers": ["file_debug", "console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
    },
}
