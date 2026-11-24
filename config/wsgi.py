import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()

# Ensure database tables exist on serverless cold starts (especially when using /tmp SQLite)
if os.environ.get("VERCEL"):
    try:
        from django.core.management import call_command
        call_command("migrate", interactive=False)
    except Exception as exc:
        print(f"Auto-migrate skipped/warning: {exc}")

app = application