"""Build a static, browse-only copy of the site into build/ for Netlify.

Run `flask --app run seed` first, then `python freeze.py`.
"""
import os
import warnings

from flask_frozen import Freezer, MimetypeMismatchWarning

from app import create_app
from app.models import Listing

BUILD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")

# Show every listing on one page, since ?page=2 links can't work on a static host.
app = create_app({"STATIC_PREVIEW": True, "LISTINGS_PER_PAGE": 100})
app.config["FREEZER_DESTINATION"] = BUILD_DIR
# Only freeze pages we list (plus every no-argument GET page), so form-only
# URLs like /cart/add/1 are skipped instead of failing the build.
freezer = Freezer(app, log_url_for=False)


@freezer.register_generator
def listing_pages():
    for listing in Listing.query.all():
        yield "shop.listing_detail", {"listing_id": listing.id}


if __name__ == "__main__":
    # Pages like /cart are saved without an extension; we fix that below.
    warnings.simplefilter("ignore", MimetypeMismatchWarning)
    freezer.freeze()

    # Rename "cart" to "cart.html" etc. Netlify serves /cart from cart.html.
    for root, _dirs, files in os.walk(BUILD_DIR):
        for name in files:
            if "." not in name:
                path = os.path.join(root, name)
                os.rename(path, path + ".html")
    print(f"Static site written to {BUILD_DIR}")