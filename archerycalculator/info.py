"""Information about handicaps and classifications page."""

from flask import (
    Blueprint,
    render_template,
)

bp = Blueprint("info", __name__, url_prefix="/info")


# Single page (for now)
@bp.route("/", strict_slashes=False)
def info():
    """Generate info page."""
    return render_template(
        "info.html",
    )
