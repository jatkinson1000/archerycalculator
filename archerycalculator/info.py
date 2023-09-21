"""Module holding routines for info page."""
from flask import (
    Blueprint,
    render_template,
)


bp = Blueprint("info", __name__, url_prefix="/info")


# Single page (for now)
@bp.route("/", strict_slashes=False)
def info():
    """
    Generate the info page in the flask app.

    Parameters
    ----------
    None

    Returns
    -------
    html template :
        template for the info page

    """
    return render_template(
        "info.html",
    )
