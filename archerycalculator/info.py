from flask import (
    Blueprint,
    render_template,
)


bp = Blueprint("info", __name__, url_prefix="/info")


# Single page (for now)
@bp.route("/", strict_slashes=False)
def info():
    # return html
    return render_template(
        "info.html",
    )
