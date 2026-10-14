"""Database tables, defined as Python classes (SQLAlchemy models)."""
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db

CATEGORIES = ["Tops", "Bottoms", "Dresses", "Outerwear", "Shoes", "Accessories"]
SIZES = ["XS", "S", "M", "L", "XL", "One Size"]
CONDITIONS = ["New with tags", "Like new", "Good", "Fair"]


def utcnow():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    listings = db.relationship("Listing", back_populates="seller", lazy="dynamic")
    orders = db.relationship("Order", back_populates="buyer", lazy="dynamic")

    def set_password(self, password):
        # Never store plain-text passwords; store a salted hash instead.
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default="")
    brand = db.Column(db.String(60), default="")
    category = db.Column(db.String(30), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    condition = db.Column(db.String(30), nullable=False)
    price_cents = db.Column(db.Integer, nullable=False)  # store money as integer cents
    image_filename = db.Column(db.String(200))
    is_sold = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    seller_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    seller = db.relationship("User", back_populates="listings")
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"))

    @property
    def price(self):
        return f"${self.price_cents / 100:,.2f}"


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_cents = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    buyer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    buyer = db.relationship("User", back_populates="orders")
    items = db.relationship("Listing", backref="order")

    @property
    def total(self):
        return f"${self.total_cents / 100:,.2f}"
