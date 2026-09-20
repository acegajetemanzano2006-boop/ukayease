# UkayEase — Ukay-Ukay Management System

A beginner-friendly, clean, and fully functional web-based inventory and sales management system tailored for a small ukay-ukay (thrift) store. Built with **Python**, **Flask**, and **SQLite**.

## Features

- **Authentication** — Secure login with hashed passwords (Werkzeug)
- **Dashboard** — Live metrics: total products, available items, sold items, total revenue
- **Product Management** — Add, edit, delete, search, and filter by category
- **Sales (POS-style)** — Record sales, auto-deduct stock, auto-update status
- **Reports** — Daily sales summary, KPIs, interactive Chart.js revenue chart
- **Thrift aesthetic** — Cream/beige UI with earthy brown accents

## Requirements

- Python 3.10+ (tested on 3.11)
- Flask ≥ 3.0
- Werkzeug ≥ 3.0

## Installation

```bash
# 1. Navigate to the project folder
cd ukayease

# 2. (Optional) Create a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py
```

Open your browser at **http://127.0.0.1:5000**

## Default Credentials

| Field    | Value    |
|----------|----------|
| Username | `admin`  |
| Password | `admin123` |

> The SQLite database `ukayease.db` is created automatically on first launch and seeded with 5 sample thrift products.

## Project Structure

```
ukayease/
├── app.py                 # Flask application & routes
├── requirements.txt
├── README.md
├── ukayease.db            # Created on first run
├── static/
│   ├── css/style.css      # Thrift-store theme
│   └── js/script.js       # Sales calculator, filters, chart
└── templates/
    ├── base.html
    ├── login.html
    ├── dashboard.html
    ├── products.html
    ├── add_product.html
    ├── edit_product.html
    ├── sales.html
    └── reports.html
```

## Routes

| Method | Path                     | Description                    | Auth |
|--------|--------------------------|--------------------------------|------|
| GET    | `/`                      | Redirect to dashboard/login    | —    |
| GET/POST | `/login`               | Login page                     | No   |
| GET    | `/logout`                | Clear session                  | Yes  |
| GET    | `/dashboard`             | Metrics & recent activity      | Yes  |
| GET    | `/products`              | Product list (search/filter)   | Yes  |
| GET/POST | `/add-product`         | Add new product                | Yes  |
| GET/POST | `/edit-product/<id>`   | Edit existing product          | Yes  |
| POST   | `/delete-product/<id>`   | Delete product                 | Yes  |
| GET/POST | `/sales`               | Record sale & view history     | Yes  |
| GET    | `/reports`               | KPIs, daily summary, chart     | Yes  |

## How Sales Work

1. Select a product that still has stock.
2. Enter quantity (capped at available stock).
3. Optionally enter customer name (defaults to “Walk-in”).
4. Confirm sale date.
5. On submit:
   - Inventory quantity is reduced.
   - If quantity reaches 0, status becomes **Sold**.
   - A sales record is inserted.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: Flask` | Run `pip install -r requirements.txt` |
| Port 5000 already in use | Change `port=5000` in `app.py` or stop the other process |
| Database locked | Close any other program that has `ukayease.db` open |
| Blank page after login | Check browser console; ensure static files are served |
| Chart not showing | Confirm internet access for Chart.js CDN, or that sales exist |

## Sample Products (seeded on first run)

1. Vintage Levi's Denim Jacket — Jacket — M — ₱450.00
2. Floral Summer Dress — Dress — S — ₱280.00
3. Classic White T-Shirt — T-Shirt — L — ₱120.00
4. High-Waist Mom Jeans — Pants — 28 — ₱350.00
5. Leather Crossbody Bag — Bag — One Size — ₱520.00

## License

This project is intended for educational / student project use.
