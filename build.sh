#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py shell -c "import os; from django.contrib.sites.models import Site; domain = os.environ.get('PUBLIC_SITE_DOMAIN') or os.environ.get('RENDER_EXTERNAL_HOSTNAME') or 'ihub-vfxz.onrender.com'; site = Site.objects.get_or_create(pk=1, defaults={'domain': domain, 'name': 'TechStore KE'})[0]; site.domain = domain; site.name = 'TechStore KE'; site.save()"

if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ]; then
  if [ "$(python manage.py shell -c "import os; from django.contrib.auth import get_user_model; User = get_user_model(); print('yes' if User.objects.filter(username=os.environ['DJANGO_SUPERUSER_USERNAME']).exists() else 'no')")" = "no" ]; then
    python manage.py createsuperuser --noinput
  fi
fi
