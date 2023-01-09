from flask import (
    Blueprint,
    render_template,
)


bp = Blueprint("about", __name__, url_prefix="/about")


# Single page (for now)
@bp.route("/")
def about():
    # return html
    return render_template(
        "about.html",
        error=None,
    )
