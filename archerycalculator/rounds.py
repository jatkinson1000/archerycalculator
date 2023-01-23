from flask import (
    Blueprint,
    render_template,
    request,
)
import numpy as np

from archerycalculator.db import query_db, sql_to_dol

from archeryutils import rounds as au_rounds

from archerycalculator import ExtrasForm, utils

bp = Blueprint("rounds", __name__, url_prefix="/rounds")
@bp.route("/", strict_slashes=False)
def rounds_page():

    rounds={}

    rounds["AGB Outdoor"] = sql_to_dol(
        query_db(
            "SELECT code_name,round_name FROM rounds WHERE location IN ('outdoor') AND body in ('AGB')"
        )
    )

    rounds["WA Outdoor"] = sql_to_dol(
        query_db(
            "SELECT code_name,round_name FROM rounds WHERE location IN ('outdoor') AND body in ('WA')"
        )
    )

    rounds["AGB Indoor"] = sql_to_dol(
        query_db(
            "SELECT code_name,round_name FROM rounds WHERE location IN ('indoor') AND body in ('AGB')"
        )
    )

    rounds["WA Indoor"] = sql_to_dol(
        query_db(
            "SELECT code_name,round_name FROM rounds WHERE location IN ('indoor') AND body in ('WA')"
        )
    )

    rounds["WA Field"] = sql_to_dol(
        query_db(
            "SELECT code_name,round_name FROM rounds WHERE location IN ('field') AND body in ('WA')"
        )
    )

    rounds["IFAA Field"] = sql_to_dol(
        query_db(
            "SELECT code_name,round_name FROM rounds WHERE location IN ('field') AND body in ('IFAA')"
        )
    )

    rounds["AGB VI"] = sql_to_dol(
        query_db(
            "SELECT code_name,round_name FROM rounds WHERE body in ('AGB-VI')"
        )
    )

    rounds["WA VI"] = sql_to_dol(
        query_db(
            "SELECT code_name,round_name FROM rounds WHERE body in ('WA-VI')"
        )
    )

    for roundtype in rounds:
        roundsdict = dict(zip(rounds[roundtype]["code_name"], rounds[roundtype]["round_name"]))
        noncompoundroundnames = utils.indoor_display_filter(roundsdict)
        codenames = [
            key
            for key in list(roundsdict.keys())
            if roundsdict[key] in noncompoundroundnames
        ]
        rounds[roundtype] = {"code_name": codenames, "round_name": noncompoundroundnames}

    return render_template("rounds.html", rounds=rounds, error=None)
