"""Information about archerycalculator.co.uk."""

from flask import (
    Blueprint,
    render_template,
)

bp = Blueprint("about", __name__, url_prefix="/about")


# Single page (for now)
@bp.route("/", strict_slashes=False)
def about():
    """Generate about page."""
    return render_template(
        "about.html",
        error=None,
    )
