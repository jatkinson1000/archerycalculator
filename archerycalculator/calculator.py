from flask import (
    Blueprint,
    render_template,
    request,
)

from archerycalculator.db import query_db, sql_to_dol

from archeryutils import rounds
from archeryutils.handicaps import handicap_equations as hc_eq
from archeryutils.handicaps import handicap_functions as hc_func
from archeryutils.classifications import classifications as class_func

from archerycalculator import HCForm

bp = Blueprint("calculator", __name__, url_prefix="/")


# Single home page (for now)
@bp.route("/", methods=("GET", "POST"))
def calculator():

    # Set form choices
    bowstylelist = sql_to_dol(query_db("SELECT bowstyle,disciplines FROM bowstyles"))[
        "bowstyle"
    ]
    genderlist = sql_to_dol(query_db("SELECT gender FROM genders"))["gender"]
    roundnames = sql_to_dol(query_db("SELECT round_name FROM rounds"))["round_name"]
    agelist = sql_to_dol(query_db("SELECT age_group FROM ages"))["age_group"]

    # Load form and set defaults
    form = HCForm.HCForm(
        request.form,
        bowstyle=bowstylelist[1],
        gender=genderlist[1],
        age=agelist[1],
    )

    # Set form choices
    form.bowstyle.choices = bowstylelist
    form.gender.choices = genderlist
    form.age.choices = agelist

    if request.method == "POST" and form.validate():
        error = None

        # Get essential form results
        bowstyle = request.form["bowstyle"]
        gender = request.form["gender"]
        age = request.form["age"]
        roundname = request.form["roundname"]
        score = request.form["score"]

        resultskeys = ["bowstyle", "gender", "age", "roundname", "score"]
        results = dict(zip(resultskeys, [None] * len(resultskeys)))

        # advanced options
        diameter = float(request.form["diameter"]) * 1.0e-3
        scheme = request.form["scheme"]
        integer_precision = True
        if request.form.getlist("decimalHC"):
            integer_precision = False
            results["decimalHC"] = True
        if diameter == 0.0:
            diameter = None

        # Check the inputs are all valid
        bowstylecheck = query_db(
            "SELECT id FROM bowstyles WHERE bowstyle IS (?)", [bowstyle]
        )
        if len(bowstylecheck) == 0:
            error = "Invalid bowstyle. Please select from dropdown."
        results["bowstyle"] = bowstyle

        gendercheck = query_db("SELECT id FROM genders WHERE gender IS (?)", [gender])
        if len(gendercheck) == 0:
            error = "Please select gender from dropdown options."
        results["gender"] = gender

        agecheck = query_db("SELECT id FROM ages WHERE age_group IS (?)", [age])
        if len(agecheck) == 0:
            error = "Invalid age group. Please select from dropdown."
        results["age"] = age

        roundcheck = query_db(
            "SELECT id FROM rounds WHERE round_name IS (?)", [roundname]
        )
        if len(roundcheck) == 0:
            error = "Invalid round name. Please select from dropdown."
        results["roundname"] = roundname

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
        # Get the appropriate round from the database
        round_db_info = query_db(
            "SELECT * FROM rounds WHERE round_name IS (?)",
            [roundname],
            one=True,
            )
        round_codename = round_db_info["code_name"]
        round_location = round_db_info["location"]
        round_obj = all_rounds_objs[round_codename]

        # Generate the handicap params
        hc_params = hc_eq.HcParams()

        # Check score against maximum score and return error if inappropriate
        max_score = round_obj.max_score()
        if int(score) <= 0:
            error = "A score of 0 or less is not valid."
        elif int(score) > max_score:
            error = (
                f"{score} is larger than the maximum possible "
                f"score of {int(max_score)} for a {roundname}."
            )
        results["score"] = score
        results["maxscore"] = int(max_score)

        if error is None:
            # Calculate the handicap
            hc_from_score = hc_func.handicap_from_score(
                float(score),
                round_obj,
                scheme,
                hc_params,
                arw_d=diameter,
                int_prec=True,
            )
            results["handicap"] = hc_from_score

            if not integer_precision:
                decimal_hc_from_score = hc_func.handicap_from_score(
                    float(score),
                    round_obj,
                    scheme,
                    hc_params,
                    arw_d=diameter,
                    int_prec=integer_precision,
                )
                results["decimal_handicap"] = decimal_hc_from_score

            # Calculate the classification
            if round_location in ['outdoor']:
                class_from_score = class_func.calculate_AGB_outdoor_classification(
                    round_codename,
                    float(score),
                    bowstyle.lower(),
                    gender.lower(),
                    age.lower(),
                )
                class_from_score = query_db(
                    "SELECT longname FROM classes WHERE shortname IS (?)",
                    [class_from_score],
                    one=True,
                )["longname"]
                results["classification"] = class_from_score
            elif round_location in ['indoor']:
                class_from_score = class_func.calculate_AGB_indoor_classification(
                    round_codename,
                    float(score),
                    bowstyle.lower(),
                    gender.lower(),
                    age.lower(),
                        )
                results["classification"] = class_from_score
            else:
                results["classification"] = "not currently available for this round"

            # Other stats
            RAD2DEG = 57.295779513
            sig_t = hc_eq.sigma_t(hc_from_score, scheme, 0.0, hc_params)
            sig_r_18 = hc_eq.sigma_r(hc_from_score, scheme, 18.0, hc_params)
            sig_r_50 = hc_eq.sigma_r(hc_from_score, scheme, 50.0, hc_params)
            sig_r_70 = hc_eq.sigma_r(hc_from_score, scheme, 70.0, hc_params)

            # Perform calculations and return the results
            return render_template(
                "calculator.html",
                form=form,
                rounds=roundnames,
                results=results,
                sig_t=2.0 * RAD2DEG * sig_t,
                sig_r_18=2.0 * 100.0 * sig_r_18,
                sig_r_50=2.0 * 100.0 * sig_r_50,
                sig_r_70=2.0 * 100.0 * sig_r_70,
            )
        else:
            # If errors reload default with error message
            return render_template(
                "calculator.html",
                form=form,
                rounds=roundnames,
                results=None,
                error=error,
            )

    # If first visit load the default form with no inputs
    return render_template(
        "calculator.html",
        form=form,
        rounds=roundnames,
        results=None,
        error=None,
    )
