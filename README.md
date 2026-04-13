# 🛒 ShopHub — E-Commerce Flask App

A full-featured e-commerce web application built with **Flask**, **SQLAlchemy**, and **Tailwind CSS**. Includes a complete customer storefront, admin dashboard, order management, email notifications, and Telegram alerts.

---

## ✨ Features

| Area | What's included |
|---|---|
| **Auth** | Register, email verification, login, forgot/reset password |
| **Shop** | Product listing, search, category browsing, product detail |
| **Cart** | Add / remove / update quantities, free shipping threshold |
| **Checkout** | Multi-field form, stock validation, order confirmation email |
| **Orders** | Order history, invoice PDF download |
| **Wishlist** | Add / remove products, persistent across sessions |
| **Notifications** | In-app bell, unread badge, mark read, delete |
| **Support** | Contact form, Telegram alert to admin, auto-reply email |
| **Admin** | Dashboard KPIs, order status management, product/category/user CRUD, support inbox, broadcast notifications |
| **Email** | Welcome, email verify, password reset, order invoice, support auto-reply |
| **Telegram** | New order alert, support message alert, low stock warning |

---

## 🚀 Quick Start

### 1 — Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/E-Commerce_Flask_App.git
cd E-Commerce_Flask_App
```

### 2 — Create and activate virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### 4 — Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```env
SECRET_KEY=your-secret-key          # python -c "import secrets; print(secrets.token_hex(32))"
FLASK_ENV=development
MAIL_USERNAME=your-gmail@gmail.com
MAIL_PASSWORD=your-app-password     # Gmail App Password (not account password)
BASE_URL=http://localhost:5000
TELEGRAM_BOT_TOKEN=                 # from @BotFather
TELEGRAM_CHAT_ID=                   # your chat ID
```

> **Gmail App Password**: Go to [myaccount.google.com](https://myaccount.google.com) → Security → 2-Step Verification → App Passwords → generate one for "Mail / Windows Computer".

### 5 — Set up the database

```bash
flask db upgrade
```

### 6 — Seed sample data (optional)

```bash
python seed.py
```

This creates sample categories, products, and an admin account.

### 7 — Run the app

```bash
flask run
```

Open [http://localhost:5000](http://localhost:5000)

---

## 🔑 Default Admin Account

After running `seed.py`:

| Field | Value |
|---|---|
| Email | `admin@shophub.com` |
| Password | `Admin@123` |

> Change the admin password immediately after first login via **Forgot Password**.

---

## 🧪 Testing All Features

### Customer flow

| Step | What to do | URL |
|---|---|---|
| 1 | Register a new account | `/auth/register` |
| 2 | Check your email → click **Verify My Email** | (email inbox) |
| 3 | Log in with your new account | `/auth/login` |
| 4 | Browse products and add to cart | `/products/` |
| 5 | Add items to wishlist | any product card |
| 6 | Go to cart, review items | `/cart/` |
| 7 | Complete checkout | `/orders/checkout` |
| 8 | View order history | `/account/orders` |
| 9 | Download invoice PDF | order history page |
| 10 | Check notification bell | navbar bell icon |
| 11 | Submit a support message | `/support` |
| 12 | Test forgot password | `/auth/forgot-password` |

### Admin flow

| Step | What to do | URL |
|---|---|---|
| 1 | Log in as admin | `/auth/login` |
| 2 | View dashboard KPIs | `/admin/dashboard` |
| 3 | Change an order status (pending → shipped) | `/admin/orders` → View order |
| 4 | Verify the customer gets a bell notification | (log in as customer) |
| 5 | Add a new product | `/admin/products/new` |
| 6 | Add a new category | `/admin/categories/new` |
| 7 | Manage users (verify / promote to admin) | `/admin/users` |
| 8 | View support inbox | `/admin/support` |
| 9 | Send a broadcast notification to all users | `/admin/dashboard` → Broadcast button |
| 10 | Download a customer's invoice | `/admin/orders/<id>` → Invoice PDF |

---

## 📁 Project Structure

```
E-Commerce_Flask_App/
├── app/
│   ├── __init__.py              # App factory, blueprints, error handlers
│   ├── core/
│   │   ├── config.py            # All settings (env-based)
│   │   ├── extensions.py        # db, mail, login_manager
│   │   └── base_service.py      # Shared CRUD base class
│   ├── modules/
│   │   ├── auth/                # Register, login, verify, reset password
│   │   ├── products/            # Product listing, search, detail
│   │   ├── categories/          # Category browsing
│   │   ├── cart/                # Shopping cart
│   │   ├── orders/              # Checkout, order history, invoice PDF
│   │   ├── wishlist/            # Saved products
│   │   ├── notifications/       # In-app bell notifications
│   │   ├── support/             # Contact form
│   │   ├── users/               # Account pages
│   │   └── admin/               # Admin dashboard
│   ├── shared/
│   │   ├── constants.py         # OrderStatus, thresholds, etc.
│   │   ├── email_service.py     # Flask-Mail wrappers
│   │   ├── telegram_service.py  # Telegram Bot API
│   │   ├── decorators.py        # @admin_required, @anonymous_required
│   │   └── marshmallow_utils.py # Shared validation helpers
│   ├── templates/
│   │   ├── master.html          # Base layout
│   │   ├── admin/               # Admin templates
│   │   ├── front/               # Customer-facing pages
│   │   ├── email/               # Email templates
│   │   └── partials/            # Reusable components
│   └── static/                  # CSS, JS, images, uploads
├── migrations/                  # Flask-Migrate DB migrations
├── instance/                    # SQLite database (git-ignored)
├── seed.py                      # Sample data seeder
├── run.py                       # App entry point
├── requirements.txt
├── .env.example                 # Environment template
└── .gitignore
```

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Flask 3.x |
| Database | SQLAlchemy + Flask-Migrate (SQLite dev / PostgreSQL prod) |
| Auth | Flask-Login, Werkzeug password hashing |
| Validation | Marshmallow |
| Email | Flask-Mail → Gmail SMTP |
| Notifications | Telegram Bot API |
| PDF | ReportLab |
| Frontend | Jinja2 templates, Tailwind CSS, Bootstrap Icons |
| Deployment | Any WSGI server (Gunicorn, uWSGI) |

---

## 📧 Email Setup (Gmail)

1. Enable **2-Step Verification** on your Google account
2. Go to [myaccount.google.com](https://myaccount.google.com) → Security → App passwords
3. Generate a password for **Mail / Windows Computer**
4. Copy the 16-character password (no spaces) into `.env` as `MAIL_PASSWORD`

---

## 🤖 Telegram Setup

1. Message **@BotFather** on Telegram → `/newbot` → follow prompts → copy the token
2. Message your new bot (send any message)
3. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
4. Find `"chat"` → `"id"` in the response — that is your `TELEGRAM_CHAT_ID`
5. Add both values to `.env`

---

## 🗄 Database Commands

```bash
# Create all tables (first time)
flask db upgrade

# After changing any model
flask db migrate -m "describe what changed"
flask db upgrade

# Reset database completely
flask db downgrade base
flask db upgrade
python seed.py
```

---

## 📦 Requirements

```bash
# Install
pip install -r requirements.txt

# Freeze current packages
pip freeze > requirements.txt
```

Key packages: `flask`, `flask-sqlalchemy`, `flask-migrate`, `flask-login`,
`flask-mail`, `marshmallow`, `reportlab`, `requests`, `python-dotenv`

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

*Built with ❤️ using Flask*