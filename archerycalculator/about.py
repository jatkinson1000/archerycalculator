"""Module holding routines for about page."""
from flask import (
    Blueprint,
    render_template,
)


bp = Blueprint("about", __name__, url_prefix="/about")


# Single page (for now)
@bp.route("/", strict_slashes=False)
def about():
    """
    Generate the about page in the flask app.

    Parameters
    ----------
    None

    Returns
    -------
    html template :
        template for the about page

    """
    return render_template(
        "about.html",
    )
