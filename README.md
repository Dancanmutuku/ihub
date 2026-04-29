# 🖥️ TechStore KE

Kenya's premier e-commerce platform for PC components, GPUs, RAM, NICs and tech gadgets. Built with **Django 5**, **Bootstrap 5**, **Google OAuth**, and **M-Pesa Daraja API** (STK Push).

---

## 🚀 Features

- **Product catalogue** — categories, search, filtering, sorting
- **Shopping cart** — session-based cart with qty management
- **Checkout** — delivery form with all 47 Kenyan counties
- **M-Pesa STK Push** — Daraja API integration for payments
- **Google Sign-In** — via django-allauth
- **User accounts** — order history, order detail
- **Admin dashboard** — full product/order management
- **Dark cyber UI** — responsive Bootstrap 5 + custom CSS
- **Seed data** — 15 products across 6 categories with Unsplash images

---

## 📁 Project Structure

```
techstore/
├── techstore/          # Django project settings
│   ├── settings.py
│   └── urls.py
├── store/              # Products, categories, reviews
├── cart/               # Session-based cart
├── orders/             # Checkout and order management
├── payments/           # M-Pesa Daraja STK Push
├── static/
│   ├── css/custom.css
│   └── js/main.js
├── templates/          # All HTML templates
├── .env.example        # ← Copy this to .env and fill in values
├── .gitignore          # .env is excluded from git
└── requirements.txt
```

---

## ⚙️ Local Setup

### 1. Clone and enter the project

```bash
git clone https://github.com/YOUR_USERNAME/techstore.git
cd techstore
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key — generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `True` for development, `False` for production |
| `DATABASE_URL` | Optional. Leave blank for local SQLite, or set a PostgreSQL connection string |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated list such as `http://localhost:8000,https://your-app.onrender.com` |
| `GOOGLE_CLIENT_ID` | From [Google Cloud Console](https://console.cloud.google.com/) |
| `GOOGLE_CLIENT_SECRET` | From Google Cloud Console |
| `MPESA_CONSUMER_KEY` | From [Safaricom Developer Portal](https://developer.safaricom.co.ke/) |
| `MPESA_CONSUMER_SECRET` | From Safaricom Developer Portal |
| `MPESA_SHORTCODE` | Use `174379` for sandbox |
| `MPESA_PASSKEY` | Sandbox passkey from Safaricom |
| `MPESA_CALLBACK_URL` | Your public URL + `/payments/mpesa/callback/` |
| `BREVO_API_KEY` | Brevo transactional email API key for production email sending |
| `DEFAULT_FROM_EMAIL` | Must use a sender email verified in Brevo |

### 5. Run migrations and load seed data

```bash
python manage.py migrate
python manage.py loaddata store/fixtures/initial_data.json
```

### 6. Create a superuser (admin)

```bash
python manage.py createsuperuser
```

### 7. Run the development server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000** 🎉

### Optional: run locally with PostgreSQL

If you want to match production more closely, set `DATABASE_URL` in `.env`:

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/techstore
```

---

## 🔑 Google OAuth Setup

1. Go to [console.cloud.google.com](https://console.cloud.google.com/)
2. Create a new project → **APIs & Services** → **Credentials**
3. Create **OAuth 2.0 Client ID** (Web Application)
4. Add `http://localhost:8000` to **Authorized JavaScript origins**
5. Add `http://localhost:8000/accounts/google/login/callback/` to **Authorized redirect URIs**
6. Copy **Client ID** and **Client Secret** into your `.env`
7. In Django admin → **Sites** → set domain to `localhost:8000`
8. In Django admin → **Social Applications** → Add Google with your credentials and select the site

---

## 📱 M-Pesa (Daraja) Setup

### Sandbox Testing

1. Register at [developer.safaricom.co.ke](https://developer.safaricom.co.ke/)
2. Create an app → get **Consumer Key** and **Consumer Secret**
3. Use Shortcode `174379` and the sandbox passkey from Daraja docs
4. For `MPESA_CALLBACK_URL`, use [ngrok](https://ngrok.com/) to expose localhost:
   ```bash
   ngrok http 8000
   # Use the https URL: https://xxxx.ngrok.io/payments/mpesa/callback/
   ```

### Sandbox Test Phone Numbers
Use Safaricom simulator test numbers: `254726263888`

---

## 🛡️ Security Notes

- **Never commit `.env`** — it is in `.gitignore`
- The `.env.example` file is safe to commit (contains no real secrets)
- For production, set `DEBUG=False` and configure proper `ALLOWED_HOSTS`
- Use environment variables (not hardcoded values) for all secrets

---

## Render Deployment

This project is ready for Render with:

- `render.yaml` for Blueprint deploys
- `build.sh` for install, static collection, and migrations
- `DATABASE_URL`-based database config with PostgreSQL support

### Option 1: Blueprint deploy

1. Push this repo to GitHub/GitLab/Bitbucket
2. In Render, open **Blueprints**
3. Create a new Blueprint using this repo
4. Review the generated services from `render.yaml`
5. Add your missing environment variables in Render:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `MPESA_CONSUMER_KEY`
   - `MPESA_CONSUMER_SECRET`
   - `MPESA_SHORTCODE`
   - `MPESA_PASSKEY`
   - `MPESA_CALLBACK_URL`
   - `MPESA_ENVIRONMENT`
   - `BREVO_API_KEY`
   - `DEFAULT_FROM_EMAIL`
   - `ADMIN_NOTIFICATION_EMAILS`
   - optional: `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD`

### Option 2: Manual Render setup

1. Create a **Postgres** database in Render
2. Copy its **internal database URL**
3. Create a **Python Web Service**
4. Use:
   - Build Command: `./build.sh`
   - Start Command: `gunicorn techstore.wsgi:application`
5. Add these environment variables:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `DEBUG=False`
   - `ALLOWED_HOSTS`
   - `CSRF_TRUSTED_ORIGINS`
   - optional: `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD`
   - plus your Google, M-Pesa, and Brevo API credentials

### After first deploy

You can either let `build.sh` create the admin automatically with:

```bash
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=adm:/2025
```

or create one manually from the Render shell:

```bash
python manage.py createsuperuser
```

If you are moving existing data from SQLite to PostgreSQL, export and import your data before going live.

---

## 🗄️ Admin Panel

Visit **http://127.0.0.1:8000/admin/** to:

- Add/edit products and categories
- Manage orders and update status
- View payment records
- Manage users

---

## 🔧 Common Commands

```bash
# Create new migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Collect static files (for production)
python manage.py collectstatic

# Load initial product data
python manage.py loaddata store/fixtures/initial_data.json

# Django shell
python manage.py shell
```

---

## 📦 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.0 |
| Auth | django-allauth + Google OAuth |
| Database | SQLite locally, PostgreSQL on Render/production |
| Frontend | Bootstrap 5 + Custom CSS (dark theme) |
| Fonts | Orbitron + Inter + JetBrains Mono |
| Payments | M-Pesa Daraja API (STK Push) |
| Secrets | python-decouple (.env) |

---

## 📝 License

MIT — feel free to fork and adapt for your own Kenyan e-commerce project.
