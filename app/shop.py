"""Storefront routes: browse, view, sell, cart, and checkout."""
import os
import uuid

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from . import db
from .forms import ListingForm
from .models import CATEGORIES, SIZES, Listing, Order

bp = Blueprint("shop", __name__)

SORTS = {
    "newest": Listing.created_at.desc(),
    "price_low": Listing.price_cents.asc(),
    "price_high": Listing.price_cents.desc(),
}


@bp.route("/")
def index():
    query = Listing.query.filter_by(is_sold=False)

    search = request.args.get("q", "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(
            Listing.title.ilike(like) | Listing.brand.ilike(like) | Listing.description.ilike(like)
        )

    category = request.args.get("category")
    if category in CATEGORIES:
        query = query.filter_by(category=category)

    size = request.args.get("size")
    if size in SIZES:
        query = query.filter_by(size=size)

    sort = request.args.get("sort", "newest")
    query = query.order_by(SORTS.get(sort, SORTS["newest"]))

    page = request.args.get("page", 1, type=int)
    pagination = query.paginate(page=page, per_page=12, error_out=False)

    return render_template(
        "shop/index.html",
        listings=pagination.items,
        pagination=pagination,
        categories=CATEGORIES,
        sizes=SIZES,
        filters={"q": search, "category": category, "size": size, "sort": sort},
    )


@bp.route("/listing/<int:listing_id>")
def listing_detail(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    in_cart = listing.id in session.get("cart", [])
    return render_template("shop/detail.html", listing=listing, in_cart=in_cart)


def _save_image(file_storage):
    """Save an uploaded image under a random name and return that name."""
    if not file_storage or not file_storage.filename:
        return None
    ext = os.path.splitext(secure_filename(file_storage.filename))[1].lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    file_storage.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
    return filename


@bp.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    form = ListingForm()
    if form.validate_on_submit():
        listing = Listing(
            title=form.title.data,
            brand=form.brand.data or "",
            category=form.category.data,
            size=form.size.data,
            condition=form.condition.data,
            price_cents=int(form.price.data * 100),
            description=form.description.data or "",
            image_filename=_save_image(form.image.data),
            seller=current_user,
        )
        db.session.add(listing)
        db.session.commit()
        flash("Your item is live!", "success")
        return redirect(url_for("shop.listing_detail", listing_id=listing.id))
    return render_template("shop/sell.html", form=form)


@bp.route("/listing/<int:listing_id>/delete", methods=["POST"])
@login_required
def delete_listing(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    if listing.seller_id != current_user.id:
        abort(403)
    if listing.is_sold:
        flash("Sold items can't be removed.", "error")
        return redirect(url_for("shop.dashboard"))
    db.session.delete(listing)
    db.session.commit()
    flash("Listing removed.", "info")
    return redirect(url_for("shop.dashboard"))


@bp.route("/dashboard")
@login_required
def dashboard():
    listings = current_user.listings.order_by(Listing.created_at.desc()).all()
    orders = current_user.orders.order_by(Order.created_at.desc()).all()
    earned = sum(l.price_cents for l in listings if l.is_sold)
    return render_template(
        "shop/dashboard.html", listings=listings, orders=orders, earned=f"${earned / 100:,.2f}"
    )


# --- Cart -----------------------------------------------------------------
# Every item is one-of-a-kind, so the cart is just a list of listing IDs
# stored in the user's (signed) session cookie.

def _cart_listings():
    ids = session.get("cart", [])
    if not ids:
        return []
    items = Listing.query.filter(Listing.id.in_(ids), Listing.is_sold.is_(False)).all()
    # Drop anything that sold or was deleted since it was added.
    session["cart"] = [l.id for l in items]
    return items


@bp.route("/cart")
def cart():
    items = _cart_listings()
    total = sum(l.price_cents for l in items)
    return render_template("shop/cart.html", items=items, total=f"${total / 100:,.2f}")


@bp.route("/cart/add/<int:listing_id>", methods=["POST"])
def cart_add(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    if listing.is_sold:
        flash("Sorry, that item just sold.", "error")
    elif current_user.is_authenticated and listing.seller_id == current_user.id:
        flash("You can't buy your own listing.", "error")
    else:
        cart = session.get("cart", [])
        if listing.id not in cart:
            cart.append(listing.id)
            session["cart"] = cart
        flash(f"Added “{listing.title}” to your bag.", "success")
    return redirect(url_for("shop.listing_detail", listing_id=listing.id))


@bp.route("/cart/remove/<int:listing_id>", methods=["POST"])
def cart_remove(listing_id):
    session["cart"] = [i for i in session.get("cart", []) if i != listing_id]
    return redirect(url_for("shop.cart"))


@bp.route("/checkout", methods=["POST"])
@login_required
def checkout():
    items = _cart_listings()
    if not items:
        flash("Your bag is empty.", "info")
        return redirect(url_for("shop.cart"))
    if any(l.seller_id == current_user.id for l in items):
        flash("Remove your own listings from the bag before checking out.", "error")
        return redirect(url_for("shop.cart"))

    # Demo checkout: no real payment is taken. Marks items sold and records an order.
    order = Order(buyer=current_user, total_cents=sum(l.price_cents for l in items))
    db.session.add(order)
    for listing in items:
        listing.is_sold = True
        listing.order = order
    db.session.commit()
    session["cart"] = []
    return render_template("shop/order_confirmation.html", order=order)
