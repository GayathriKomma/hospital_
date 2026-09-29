from . import settings as base_settings

globals().update(
    {
        name: value
        for name, value in vars(base_settings).items()
        if name.isupper()
    }
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
