"""Routines for the main calculator page."""
from flask import (
    Blueprint,
    render_template,
    request,
)

from archeryutils import load_rounds
from archeryutils.handicaps import handicap_equations as hc_eq
from archeryutils.handicaps import handicap_functions as hc_func
import archeryutils.classifications as class_func

from archerycalculator import hc_form, utils
from archerycalculator.db import query_db, sql_to_dol


bp = Blueprint("calculator", __name__, url_prefix="/")


# Single home page (for now)
@bp.route("/", methods=("GET", "POST"))
def calculator():
    """
    Generate the calculator page in the flask app.

    Parameters
    ----------
    None

    Returns
    -------
    html template :
        template for the calculator page

    """
    # Set form choices
    bowstylelist = sql_to_dol(query_db("SELECT bowstyle,disciplines FROM bowstyles"))[
        "bowstyle"
    ]
    genderlist = sql_to_dol(query_db("SELECT gender FROM genders"))["gender"]
    roundnames = sql_to_dol(query_db("SELECT code_name,round_name FROM rounds"))
    roundnames = utils.indoor_display_filter(
        dict(zip(roundnames["code_name"], roundnames["round_name"]))
    )
    agelist = sql_to_dol(query_db("SELECT age_group FROM ages"))["age_group"]

    # Load form and set defaults
    form = hc_form.HCForm(
        request.form,
    )

    # Set form choices
    form.bowstyle.choices = [""] + bowstylelist
    form.gender.choices = [""] + genderlist
    form.age.choices = [""] + agelist
    form.roundname.choices = [""] + roundnames

    # Initialise any errors or warnings
    error = None
    warning_bowstyle = None
    warning_handicap_round = None
    warning_handicap_system = None

    if request.method == "POST" and form.validate():
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

        # Check inputs from form are valid
        results, error = check_inputs(results, bowstyle, gender, age, roundname)

        if error is None:
            # Get round info
            round_obj, round_codename, round_location, round_body = load_round(
                roundname, bowstyle
            )

            # Check for valid input score
            results, error = check_max_score(round_obj, roundname, score, results)

            if error is None:
                # Generate the handicap params
                hc_params = hc_eq.HcParams()

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

                # If decimal requested calculate and return
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
                if round_location in ["outdoor"] and round_body in ["AGB", "WA"]:
                    # Warn about bowstyle (handled by archeryutils).
                    if bowstyle.lower() in ["traditional", "flatbow", "asiatic"]:
                        warning_bowstyle = (
                            f"Note: Treating {bowstyle} as Barebow "
                            f"for the purposes of classifications."
                        )

                    class_from_score = class_func.calculate_agb_outdoor_classification(
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

                elif round_location in ["indoor"] and round_body in ["AGB", "WA"]:
                    # Warn about bowstyle (handled by archeryutils).
                    if bowstyle.lower() in ["traditional", "flatbow", "asiatic"]:
                        warning_bowstyle = (
                            f"Note: Treating {bowstyle} as Barebow "
                            "for the purposes of classifications."
                        )

                    class_from_score = class_func.calculate_agb_indoor_classification(
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

                elif round_location in ["field"] and round_body in ["AGB", "WA"]:
                    class_from_score = class_func.calculate_agb_field_classification(
                        round_codename,
                        float(score),
                        bowstyle.lower(),
                        gender.lower(),
                        age.lower(),
                    )
                    results["classification"] = class_from_score
                    warning_handicap_round = (
                        "Note: This round is not officially "
                        "recognised by Archery GB for the purposes of handicapping."
                    )

                else:
                    results["classification"] = "not currently available"
                    warning_handicap_round = (
                        "Note: This round is not officially "
                        "recognised by Archery GB for the "
                        "purposes of handicapping."
                    )

                # Other stats
                radian_to_degree = 57.295779513
                sig_t = hc_eq.sigma_t(hc_from_score, scheme, 0.0, hc_params)
                sig_r_18 = hc_eq.sigma_r(hc_from_score, scheme, 18.0, hc_params)
                sig_r_50 = hc_eq.sigma_r(hc_from_score, scheme, 50.0, hc_params)
                sig_r_70 = hc_eq.sigma_r(hc_from_score, scheme, 70.0, hc_params)

                # Perform calculations and return the results
                return render_template(
                    "calculator.html",
                    form=form,
                    results=results,
                    sig_t=2.0 * radian_to_degree * sig_t,
                    sig_r_18=2.0 * 100.0 * sig_r_18,
                    sig_r_50=2.0 * 100.0 * sig_r_50,
                    sig_r_70=2.0 * 100.0 * sig_r_70,
                    warning_bowstyle=warning_bowstyle,
                    warning_handicap_round=warning_handicap_round,
                    warning_handicap_system=warning_handicap_system,
                )

    # If errors reload page with error reports
    # If first visit load the default form with no inputs
    return render_template(
        "calculator.html",
        form=form,
        results=None,
        error=error,
    )


def check_inputs(results, bowstyle, gender, age, roundname):
    """
    Check inputs are valid and return in dict.

    Parameters
    ----------
    results : Dict[]
        Dict of results extracted from the form
    bowstyle : str
        bowstyle being used
    gender : str
        gender being used
    age : str
        age being used
    roundname : str
        name of round to use

    Returns
    -------
    results : Dict[]
        amended Dict of results extracted from the form
    error : str or None
        string containing en error message as appropriate

    """
    # Check the inputs are all valid
    # No longer need to check dropdowns, but leave in case
    error = None

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
        "SELECT * FROM rounds WHERE round_name IS (?)", [roundname], one=True
    )
    if roundcheck is None:
        error = (
            f"Invalid round name '{roundname}'. "
            f"Please start typing and select from dropdown."
        )
    results["roundname"] = roundname

    return results, error


def load_round(roundname, bowstyle):
    """
    Check inputs are valid and return in dict.

    Parameters
    ----------
    roundname : str
        name of round to use
    bowstyle : str
        bowstyle being used

    Returns
    -------
    round_obj : Round
        Round object for the appropriate round
    round_body : str
        governing body for this round
    round_codename : str
        codename for this round
    round_location : str
        location for this round

    """
    all_rounds_objs = load_rounds.read_json_to_round_dict(
        [
            "AGB_outdoor_imperial.json",
            "AGB_outdoor_metric.json",
            "AGB_indoor.json",
            "WA_outdoor.json",
            "WA_indoor.json",
            "WA_field.json",
            "IFAA_field.json",
            "AGB_VI.json",
            "WA_VI.json",
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
    round_body = round_db_info["body"]

    # Check if we need compound scoring
    if bowstyle.lower() in ["compound"]:
        round_codename = utils.get_compound_codename(round_codename)
    round_obj = all_rounds_objs[round_codename]

    return round_obj, round_codename, round_location, round_body


def check_max_score(round_obj, roundname, score, results):
    """
    Check score against maximum score and return error if inappropriate.

    Parameters
    ----------
    round_obj : Round
        Round object for the appropriate round
    roundname : str
        name of round
    score : int
        score input
    results : Dict[str: Any]
        Dict of results extracted from the form

    Returns
    -------
    results : Dict[str: Any]
        amended Dict of results extracted from the form
    error : str or None
        string containing en error message as appropriate

    """
    error = None

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

    return results, error
