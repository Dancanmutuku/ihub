#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ]; then
  if [ "$(python manage.py shell -c "import os; from django.contrib.auth import get_user_model; User = get_user_model(); print('yes' if User.objects.filter(username=os.environ['DJANGO_SUPERUSER_USERNAME']).exists() else 'no')")" = "no" ]; then
    python manage.py createsuperuser --noinput
  fi
fi
