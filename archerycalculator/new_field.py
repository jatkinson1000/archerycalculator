"""New field classification webpage."""

import copy
import numpy as np

from flask import (
    Blueprint,
    render_template,
)

from archeryutils import classifications as cf
from archerycalculator import utils
from archerycalculator.db import query_db, sql_to_dol, generate_enum_mapping

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
    bowstyle_mapping = generate_enum_mapping(cf.AGB_bowstyles, "SELECT bowstyle_enum,bowstyle FROM bowstyles")
    age_mapping = generate_enum_mapping(cf.AGB_ages, "SELECT age_enum,age_group FROM ages")
    gender_mapping = generate_enum_mapping(cf.AGB_genders, "SELECT gender_enum,gender FROM genders")

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

    for bowstyle in list(bowstyle_mapping.keys()):
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

        for gender in list(gender_mapping.keys()):
            for age in [key for key in age_mapping if key != "Under 21"]:

                results = np.zeros([len(use_rounds["code_name"]), len(classlist) - 1])
                for i, round_i in enumerate(use_rounds["code_name"]):
                    results[i, :] = np.asarray(
                        cf.agb_field_classification_scores(
                            round_i,
                            bowstyle_mapping[bowstyle],
                            gender_mapping[gender],
                            age_mapping[age],
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
