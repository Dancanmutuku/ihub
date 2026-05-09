#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py check
python manage.py showmigrations
python manage.py shell -c "import os; from django.contrib.sites.models import Site; domain = os.environ.get('PUBLIC_SITE_DOMAIN') or os.environ.get('RENDER_EXTERNAL_HOSTNAME') or 'ihub-vfxz.onrender.com'; site = Site.objects.get_or_create(pk=1, defaults={'domain': domain, 'name': 'TechStore KE'})[0]; site.domain = domain; site.name = 'TechStore KE'; site.save()"

if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
  python manage.py shell -c "import os; from django.contrib.auth import get_user_model; User = get_user_model(); username = os.environ['DJANGO_SUPERUSER_USERNAME']; email = os.environ.get('DJANGO_SUPERUSER_EMAIL', ''); password = os.environ['DJANGO_SUPERUSER_PASSWORD']; user, created = User.objects.get_or_create(username=username, defaults={'email': email, 'is_staff': True, 'is_superuser': True}); user.email = email or user.email; user.is_staff = True; user.is_superuser = True; user.set_password(password) if created or password else None; user.save(); print('Created superuser' if created else 'Updated existing superuser')"
fi
