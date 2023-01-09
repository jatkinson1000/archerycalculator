from flask import (
    Blueprint,
    render_template,
    request,
)
import numpy as np

from archerycalculator.db import get_db

from archeryutils import rounds
from archeryutils.handicaps import handicap_equations as hc_eq
from archeryutils.handicaps import handicap_functions as hc_func
from archeryutils.classifications import classifications as class_func

from archerycalculator import TableForm

bp = Blueprint("tables", __name__, url_prefix="/tables")


@bp.route("/", methods=("GET", "POST"))
def tables():

    database = get_db()

    form = TableForm.TableForm(request.form)

    all_rounds = database.execute("SELECT round_name FROM rounds").fetchall()

    if request.method == "POST" and form.validate():
        error = None

        all_rounds_objs = rounds.read_json_to_round_dict(
            [
                "AGB_outdoor_imperial.json",
                "AGB_outdoor_metric.json",
                "AGB_indoor.json",
                "WA_outdoor.json",
                "WA_indoor.json",
                "Custom.json",
            ]
        )

        # Get essential form results
        rounds_req = []
        rounds_req.append(request.form["round1"])
        rounds_req.append(request.form["round2"])
        rounds_req.append(request.form["round3"])
        rounds_req.append(request.form["round4"])
        rounds_req.append(request.form["round5"])
        rounds_req.append(request.form["round6"])
        rounds_req.append(request.form["round7"])

        rounds_req = [i for i in rounds_req if i]
        round_objs = []
        for round_i in rounds_req:
            roundcheck = database.execute(
                "SELECT id FROM rounds WHERE round_name IS (?)", [round_i]
            ).fetchall()
            if len(roundcheck) == 0:
                error = f"Invalid round name '{round_i}'. Please select from dropdown."

            # Get the appropriate rounds from the database
            round_objs.append(
                all_rounds_objs[
                    database.execute(
                        "SELECT code_name FROM rounds WHERE round_name IS (?)",
                        [round_i],
                    ).fetchone()["code_name"]
                ]
            )

        # Generate the handicap params
        hc_params = hc_eq.HcParams()

        results = np.zeros([151, len(round_objs) + 1])
        results[:, 0] = np.arange(0, 151).astype(np.int32)
        for i, round_obj_i in enumerate(round_objs):
            results[:, i + 1] = hc_eq.score_for_round(
                round_obj_i, results[:, 0], "AGB", hc_params
            )[0].astype(np.int32)

        if error is None:
            # Calculate the handicap
            # Generate table for selected rounds
            # Need to add non-outdoor rounds to database

            # Return the results
            return render_template(
                "tables.html",
                rounds=all_rounds,
                form=form,
                roundnames=rounds_req,
                results=results,
            )
        else:
            # If errors reload default with error message
            return render_template(
                "tables.html",
                rounds=all_rounds,
                form=form,
                error=error,
            )

    # If first visit load the default form with no inputs
    return render_template(
        "tables.html",
        form=form,
        rounds=all_rounds,
        error=None,
    )
