from flask import (
    Blueprint,
    render_template,
)

from archerycalculator.db import query_db, sql_to_dol

from archerycalculator import utils


bp = Blueprint("rounds", __name__, url_prefix="/rounds")


@bp.route("/", strict_slashes=False)
def rounds_page():
    rounds = {}

    rounds["AGB Outdoor"] = utils.fetch_and_sort_rounds(location="outdoor", body="AGB")

    rounds["WA Outdoor"] = utils.fetch_and_sort_rounds(location="outdoor", body="WA")

    rounds["AGB Indoor"] = utils.fetch_and_sort_rounds(location="indoor", body="AGB")

    rounds["WA Indoor"] = utils.fetch_and_sort_rounds(location="indoor", body="WA")

    rounds["WA Field"] = utils.fetch_and_sort_rounds(location="field", body="WA")

    rounds["IFAA Field"] = utils.fetch_and_sort_rounds(location="field", body="IFAA")

    # TODO These don't have a family allocated.
    # Condiser doing so or extending fetch and sort function
    rounds["AGB VI"] = sql_to_dol(
        query_db("SELECT code_name,round_name FROM rounds WHERE body in ('AGB-VI')")
    )

    rounds["WA VI"] = sql_to_dol(
        query_db("SELECT code_name,round_name FROM rounds WHERE body in ('WA-VI')")
    )

    rounds["Custom"] = sql_to_dol(
        query_db("SELECT code_name,round_name FROM rounds WHERE body in ('custom')")
    )

    for roundtype in rounds:
        roundsdict = dict(
            zip(rounds[roundtype]["code_name"], rounds[roundtype]["round_name"])
        )
        noncompoundroundnames = utils.indoor_display_filter(roundsdict)
        codenames = [
            key
            for key in list(roundsdict.keys())
            if roundsdict[key] in noncompoundroundnames
        ]
        rounds[roundtype] = {
            "code_name": codenames,
            "round_name": noncompoundroundnames,
        }

    return render_template("rounds.html", rounds=rounds, error=None)
