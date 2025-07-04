"""Lists of all rounds available on archerycalculator."""

from flask import (
    Blueprint,
    render_template,
)

from archerycalculator import utils
from archerycalculator.db import query_db, sql_to_dol

bp = Blueprint("rounds", __name__, url_prefix="/rounds")


@bp.route("/", strict_slashes=False)
def rounds_page():
    """
    Create and display a dictionary of families of rounds available compare to.

    Returns
    -------
    html template :
        template for the rounds list page
    """
    rounds = {}

    rounds["AGB Outdoor"] = utils.fetch_and_sort_rounds(location="outdoor", body="AGB")

    rounds["WA Outdoor"] = utils.fetch_and_sort_rounds(location="outdoor", body="WA")

    rounds["AGB Indoor"] = utils.fetch_and_sort_rounds(location="indoor", body="AGB")

    rounds["WA Indoor"] = utils.fetch_and_sort_rounds(location="indoor", body="WA")

    rounds["WA Field"] = utils.fetch_and_sort_rounds(location="field", body="WA")

    rounds["IFAA Field"] = utils.fetch_and_sort_rounds(location="field", body="IFAA")

    # TODO These don't have a family allocated.
    # Consider doing so or extending fetch and sort function
    rounds["AGB VI"] = sql_to_dol(
        query_db("SELECT code_name,round_name FROM rounds WHERE body in ('AGB-VI')")
    )

    rounds["WA VI"] = sql_to_dol(
        query_db("SELECT code_name,round_name FROM rounds WHERE body in ('WA-VI')")
    )

    rounds["WA Experimental"] = utils.fetch_and_sort_rounds(location="outdoor", body="WAExp")

    rounds["Custom"] = sql_to_dol(
        query_db("SELECT code_name,round_name FROM rounds WHERE body in ('custom')")
    )

    for roundfam, roundlist in rounds.items():
        roundsdict = dict(zip(roundlist["code_name"], roundlist["round_name"]))
        noncompoundroundnames = utils.indoor_display_filter(roundsdict)
        codenames = [
            key
            for key in list(roundsdict.keys())
            if roundsdict[key] in noncompoundroundnames
        ]
        rounds[roundfam] = {
            "code_name": codenames,
            "round_name": noncompoundroundnames,
        }

    return render_template("rounds.html", rounds=rounds, error=None)
