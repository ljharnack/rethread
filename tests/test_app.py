import pytest

from app import create_app, db
from app.models import Listing, Order, User


@pytest.fixture
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",  # in-memory database
        "UPLOAD_FOLDER": str(tmp_path),
    })
    with app.app_context():
        seller = User(username="seller", email="seller@example.com")
        seller.set_password("password123")
        db.session.add(seller)
        db.session.add_all([
            Listing(title="Denim Jacket", brand="Levi's", category="Outerwear", size="M",
                    condition="Good", price_cents=4500, seller=seller),
            Listing(title="Silk Scarf", brand="Hermes", category="Accessories", size="One Size",
                    condition="Like new", price_cents=9000, seller=seller),
        ])
        db.session.commit()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def register(client, username="buyer"):
    return client.post("/auth/register", data={
        "username": username, "email": f"{username}@example.com",
        "password": "password123", "confirm": "password123",
    }, follow_redirects=True)


def test_home_lists_items(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Denim Jacket" in res.data and b"Silk Scarf" in res.data


def test_filter_by_category(client):
    res = client.get("/?category=Accessories")
    assert b"Silk Scarf" in res.data
    assert b"Denim Jacket" not in res.data


def test_search(client):
    res = client.get("/?q=levi")
    assert b"Denim Jacket" in res.data
    assert b"Silk Scarf" not in res.data


def test_register_and_login(client):
    res = register(client)
    assert b"Welcome to ReThread" in res.data
    client.post("/auth/logout")
    res = client.post("/auth/login", data={"username": "buyer", "password": "password123"},
                      follow_redirects=True)
    assert b"buyer" in res.data


def test_wrong_password_rejected(client):
    res = client.post("/auth/login", data={"username": "seller", "password": "nope"})
    assert b"Incorrect username or password" in res.data


def test_sell_requires_login(client):
    res = client.get("/sell")
    assert res.status_code == 302
    assert "/auth/login" in res.headers["Location"]


def test_create_listing(client, app):
    register(client)
    res = client.post("/sell", data={
        "title": "Wool Coat", "brand": "COS", "category": "Outerwear", "size": "L",
        "condition": "Like new", "price": "120.00", "description": "Warm.",
    }, follow_redirects=True)
    assert b"Your item is live" in res.data
    with app.app_context():
        assert Listing.query.filter_by(title="Wool Coat").one().price_cents == 12000


def test_checkout_marks_items_sold(client, app):
    register(client)
    client.post("/cart/add/1")
    client.post("/cart/add/2")
    res = client.post("/checkout")
    assert b"$135.00" in res.data
    with app.app_context():
        assert Order.query.count() == 1
        assert all(l.is_sold for l in Listing.query.all())
    # Sold items disappear from the storefront.
    assert b"Denim Jacket" not in client.get("/").data


def test_cannot_buy_own_listing(client):
    client.post("/auth/login", data={"username": "seller", "password": "password123"})
    res = client.post("/cart/add/1", follow_redirects=True)
    assert b"buy your own listing" in res.data


def test_cannot_delete_someone_elses_listing(client):
    register(client)
    assert client.post("/listing/1/delete").status_code == 403
