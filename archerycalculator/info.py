from flask import (
    Blueprint,
    render_template,
)


bp = Blueprint("info", __name__, url_prefix="/info")


# Single page (for now)
@bp.route("/")
def about():
    # return html
    return render_template(
        "info.html",
    )
