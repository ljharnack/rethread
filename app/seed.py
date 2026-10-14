"""`flask seed` — fills the database with demo users and listings."""
import click
from flask.cli import with_appcontext

from . import db
from .models import Listing, Order, User

DEMO_USERS = [
    ("maya", "maya@example.com"),
    ("jordan", "jordan@example.com"),
    ("sam", "sam@example.com"),
]

# (title, brand, category, size, condition, price, description)
DEMO_LISTINGS = [
    ("Vintage Levi's 501 Jeans", "Levi's", "Bottoms", "M", "Good", 48.00,
     "Classic straight-leg 501s with natural fading. Waist 30, inseam 32."),
    ("Oversized Wool Overcoat", "COS", "Outerwear", "L", "Like new", 120.00,
     "Charcoal grey, dropped shoulders, fully lined. Worn twice."),
    ("Silk Slip Dress", "Reformation", "Dresses", "S", "Like new", 85.00,
     "Bias-cut midi slip dress in emerald green."),
    ("Chuck Taylor All Star Hi", "Converse", "Shoes", "M", "Good", 30.00,
     "Black canvas high-tops, US men's 8 / women's 10."),
    ("Cable Knit Fisherman Sweater", "J.Crew", "Tops", "M", "Good", 38.00,
     "Cream cotton-wool blend, chunky and warm."),
    ("Leather Crossbody Bag", "Madewell", "Accessories", "One Size", "Good", 65.00,
     "Cognac leather with adjustable strap. Light wear on corners."),
    ("Linen Button-Down Shirt", "Everlane", "Tops", "L", "New with tags", 42.00,
     "Relaxed fit in sage green. Never worn, tags attached."),
    ("Pleated Wide-Leg Trousers", "Aritzia", "Bottoms", "S", "Like new", 55.00,
     "High-rise, cream, flowy drape. Great for work."),
    ("90s Denim Trucker Jacket", "Lee", "Outerwear", "M", "Fair", 34.00,
     "True vintage with some fraying at the cuffs — adds character."),
    ("Floral Wrap Midi Dress", "& Other Stories", "Dresses", "M", "Good", 49.00,
     "Navy with small white florals, flutter sleeves."),
    ("Chelsea Boots", "Blundstone", "Shoes", "L", "Good", 110.00,
     "Rustic brown #585, AU size 9. Resoled last year."),
    ("Cashmere Beanie", "Uniqlo", "Accessories", "One Size", "New with tags", 18.00,
     "Heather grey 100% cashmere."),
    ("Graphic Band Tee", "Vintage", "Tops", "XL", "Fair", 26.00,
     "Faded single-stitch tee from a 1994 tour."),
    ("Corduroy Mini Skirt", "Urban Outfitters", "Bottoms", "XS", "Like new", 22.00,
     "Rust-colored wide-wale cord, A-line."),
    ("Puffer Vest", "Patagonia", "Outerwear", "S", "Good", 70.00,
     "Down-filled, forest green, packs into its own pocket."),
    ("Gold Hoop Earrings", "Mejuri", "Accessories", "One Size", "Like new", 40.00,
     "Small 14k gold vermeil hoops, comes with original pouch."),
]


@click.command("seed")
@with_appcontext
def seed_command():
    """Reset the database and load demo data."""
    db.drop_all()
    db.create_all()

    users = []
    for username, email in DEMO_USERS:
        user = User(username=username, email=email)
        user.set_password("password123")
        users.append(user)
    db.session.add_all(users)

    for i, (title, brand, category, size, condition, price, desc) in enumerate(DEMO_LISTINGS):
        db.session.add(Listing(
            title=title, brand=brand, category=category, size=size, condition=condition,
            price_cents=int(price * 100), description=desc, seller=users[i % len(users)],
        ))

    # One completed sale, so the dashboard shows order history.
    db.session.flush()
    sold = Listing.query.filter_by(title="Cashmere Beanie").one()
    order = Order(buyer=users[1], total_cents=sold.price_cents)
    sold.is_sold = True
    sold.order = order
    db.session.add(order)

    db.session.commit()
    click.echo(f"Seeded {len(users)} users and {len(DEMO_LISTINGS)} listings.")
    click.echo("Log in as maya / jordan / sam with password: password123")
