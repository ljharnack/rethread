"""`flask seed` — fills the database with demo users and listings."""
import os
import shutil

import click
from flask import current_app
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

# Listing title -> image file in app/seed_images/.
# Titles must match DEMO_LISTINGS exactly. Missing files fall back to the placeholder.
SEED_IMAGES = {
    "Vintage Levi's 501 Jeans": "rethread-levis-jeans.jpg",
    "Oversized Wool Overcoat": "rethread-wool-overcoat.jpg",
    "Silk Slip Dress": "rethread-silk-dress.jpg",
    "Chuck Taylor All Star Hi": "rethread-chuck-taylors.jpg",
    "Cable Knit Fisherman Sweater": "rethread-cable-sweater.jpg",
    "Leather Crossbody Bag": "rethread-crossbody-bag.jpg",
    "Linen Button-Down Shirt": "rethread-linen-shirt.jpg",
    "Pleated Wide-Leg Trousers": "rethread-wide-leg-trousers.jpg",
    "90s Denim Trucker Jacket": "rethread-denim-jacket.jpg",
    "Floral Wrap Midi Dress": "rethread-floral-dress.jpg",
    "Chelsea Boots": "rethread-chelsea-boots.jpg",
    "Cashmere Beanie": "rethread-cashmere-beanie.jpg",
    "Graphic Band Tee": "rethread-band-tee.jpg",
    "Corduroy Mini Skirt": "rethread-corduroy-skirt.jpg",
    "Puffer Vest": "rethread-puffer-vest.jpg",
    "Gold Hoop Earrings": "rethread-gold-hoops.jpg",
}


def copy_seed_image(filename):
    """Copy an image from seed_images/ into the upload folder.

    Returns the filename if it was copied, or None if the file is missing.
    """
    if not filename:
        return None
    source = os.path.join(current_app.root_path, "seed_images", filename)
    if not os.path.exists(source):
        click.echo(f"Missing image: {filename} (using placeholder)")
        return None
    shutil.copy(source, current_app.config["UPLOAD_FOLDER"])
    return filename


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

    # Catch typos: every key in SEED_IMAGES should be a real listing title.
    titles = {listing[0] for listing in DEMO_LISTINGS}
    for title in SEED_IMAGES:
        if title not in titles:
            click.echo(f"Warning: SEED_IMAGES has no matching listing for {title!r}")

    for i, (title, brand, category, size, condition, price, desc) in enumerate(DEMO_LISTINGS):
        filename = copy_seed_image(SEED_IMAGES.get(title))
        db.session.add(Listing(
            title=title, brand=brand, category=category, size=size, condition=condition,
            price_cents=int(price * 100), description=desc, seller=users[i % len(users)],
            image_filename=filename,
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
