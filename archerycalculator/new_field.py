"""New field classification webpage."""

import copy
import numpy as np

from flask import (
    Blueprint,
    render_template,
)

from archeryutils import classifications as class_func
from archerycalculator import utils
from archerycalculator.db import query_db, sql_to_dol

bp = Blueprint("new-field", __name__, url_prefix="/new-field")


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

    # Construct tables for all combinations in a dict

    # Send to html constructor
    tables = {}

    classlist = sql_to_dol(
        query_db("SELECT shortname FROM classes WHERE location IS 'outdoor'")
    )["shortname"]

    # use_rounds = utils.fetch_and_sort_rounds(location="field", body=['AGB','WA'])
    field_rounds = {
        "code_name": [
            "wa_field_24_red_marked",
            "wa_field_24_blue_marked",
            "wa_field_24_yellow_marked",
            "wa_field_24_white_marked",
            "wa_field_12_red_marked",
            "wa_field_12_blue_marked",
            "wa_field_12_yellow_marked",
            "wa_field_12_white_marked",
        ],
        "round_name": [
            "WA Field 24 Red",
            "WA Field 24 Blue",
            "WA Field 24 Yellow",
            "WA Field 24 White",
            "WA Field 12 Red",
            "WA Field 12 Blue",
            "WA Field 12 Yellow",
            "WA Field 12 White",
        ],
    }

    for bowstyle in [
        "compound",
        "recurve",
        "barebow",
        "traditional",
        "flatbow",
        "english longbow",
        "compound limited",
        "compound barebow",
    ]:
        use_rounds = copy.deepcopy(field_rounds)
        if bowstyle.lower().replace(" ", "") in [
            "barebow",
            "longbow",
            "englishlongbow",
            "traditional",
            "flatbow",
            "compoundbarebow",
        ]:
            use_rounds["code_name"].pop(0)
            use_rounds["round_name"].pop(0)
            use_rounds["code_name"].pop(3)
            use_rounds["round_name"].pop(3)

        for gender in ["male", "female"]:
            for age in [
                "50+",
                "adult",
                # "under21",
                "under18",
                "under16",
                "under15",
                "under14",
                "under12",
            ]:
                # Handle age groups - field has no U21
                if age.lower().replace(" ", "") in ("under21"):
                    age = "Adult"

                results = np.zeros([len(use_rounds["code_name"]), len(classlist) - 1])
                for i, round_i in enumerate(use_rounds["code_name"]):
                    results[i, :] = np.asarray(
                        class_func.agb_field_classification_scores(
                            round_i, bowstyle, gender, age
                        )
                    )

                results = np.flip(
                    np.concatenate(
                        (
                            results.astype(int),
                            np.asarray(use_rounds["round_name"])[:, None],
                        ),
                        axis=1,
                    ),
                    axis=1,
                )

                tables[f"{bowstyle} {age} {gender}"] = results.astype(str)

    classes = classlist[-2::-1]

    return render_template(
        "new_field.html",
        tables=tables,
        classes=classes,
    )
