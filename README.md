# ReThread

A secondhand clothing marketplace where users can list pre-owned items, browse and filter the catalog, add items to a bag, and check out.

> Portfolio project: checkout is simulated. No real payments are processed.

**Live demo:** https://ljharnack-rethread.netlify.app

## Features

- **Accounts**: registration and login with hashed passwords (Flask-Login)
- **Browse**: search by keyword, filter by category and size, sort by price or date, pagination
- **Sell**: create listings with photo upload, remove your own listings
- **Cart and checkout**: session-based bag; checkout records an order and marks items sold
- **Dashboard**: active and sold listings, earnings, and order history
- **Security basics**: CSRF protection on every form, open-redirect-safe login, owner-only deletes, upload type and size limits
- **Tests**: pytest suite covering auth, filtering, listing creation, and checkout

## Tech stack

| Layer     | Choice                         |
|-----------|--------------------------------|
| Backend   | Python, Flask 3                |
| Database  | SQLite via Flask-SQLAlchemy    |
| Forms     | Flask-WTF / WTForms            |
| Frontend  | Jinja2 templates, hand-written responsive CSS |
| Testing   | pytest                         |

## Run it locally

```bash
git clone https://github.com/ljharnack/rethread.git
cd rethread
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app run seed     # load demo data
flask --app run run --debug
```

Open http://127.0.0.1:5000. Demo accounts: `maya`, `jordan`, `sam` (password `password123`).

Run the tests:

```bash
pytest
```

## Project structure

```
app/
  __init__.py     # app factory, extensions, blueprint registration
  models.py       # User, Listing, Order tables
  forms.py        # form classes and validation
  auth.py         # register / login / logout routes
  shop.py         # browse, listing, sell, cart, checkout, dashboard routes
  seed.py         # `flask seed` demo-data command
  templates/      # Jinja2 HTML templates
  static/         # CSS and uploaded images
tests/            # pytest suite
run.py            # entry point
```

## Possible next steps

- Edit listings and support multiple photos per item
- Real payments with Stripe in test mode
- Favorites / wishlist
- Deploy to Render or Railway with PostgreSQL
