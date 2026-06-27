"""API endpoint for handicap calculation."""

from flask import Blueprint, jsonify, request

from archeryutils import classifications as cf
from archeryutils import handicaps as hc

from archerycalculator import calculator, utils
from archerycalculator.db import generate_enum_mapping

bp = Blueprint("api", __name__, url_prefix="/api")

VALID_SCHEMES = ("AGB", "AGBold", "AA", "AA2")


def parse_input(data) -> tuple[dict | str, int]:
    """
    Parse and validate API input data.

    Parameters
    ----------
    data : dict
        raw input data from query string or JSON body

    Returns
    -------
    validated : dict or error message : str
        validated input or error description
    status_code : int
        200 on success, 400 on validation failure
    """
    bowstyle = data.get("bowstyle")
    gender = data.get("gender")
    age = data.get("age")
    roundname = data.get("roundname")
    score = data.get("score")

    missing = [
        field
        for field in ("bowstyle", "gender", "age", "roundname", "score")
        if data.get(field) is None
    ]
    if missing:
        return f"Missing required parameters: {', '.join(missing)}", 400

    scheme = data.get("scheme", "AGB")
    if scheme not in VALID_SCHEMES:
        return f"Invalid scheme. Must be one of: {', '.join(VALID_SCHEMES)}", 400

    decimal_hc = data.get("decimalHC", False)
    if isinstance(decimal_hc, str):
        decimal_hc = decimal_hc.lower() in ("true", "1", "yes")

    try:
        diameter = float(data.get("diameter", 0.0)) * 1.0e-3
    except ValueError:
        return "Invalid diameter value", 400

    if diameter < 0:
        return "Invalid arrow diameter, must be positive", 400
    if diameter == 0.0:
        diameter = None

    return {
        "bowstyle": bowstyle,
        "gender": gender,
        "age": age,
        "roundname": roundname,
        "score": score,
        "scheme": scheme,
        "decimal_hc": decimal_hc,
        "diameter": diameter,
    }, 200


def calc_single(input_data: dict):
    """
    Perform the full handicap calculation for a single set of inputs.

    Parameters
    ----------
    input_data : dict
        validated input data from parse_input

    Returns
    -------
    result_or_error : dict
        JSON-serialisable result or error dict
    status_code : int
        200 on success, 400 on validation failure
    """
    (
        bowstyle, gender, age, roundname, score, scheme, decimal_hc, diameter
    ) = (
        input_data["bowstyle"],
        input_data["gender"],
        input_data["age"],
        input_data["roundname"],
        input_data["score"],
        input_data["scheme"],
        input_data["decimal_hc"],
        input_data["diameter"],
    )

    # Enum mappings for classification lookups
    bowstyle_mapping = generate_enum_mapping(
        cf.AGB_bowstyles, "SELECT bowstyle_enum,bowstyle FROM bowstyles"
    )
    age_mapping = generate_enum_mapping(
        cf.AGB_ages, "SELECT age_enum,age_group FROM ages"
    )
    gender_mapping = generate_enum_mapping(
        cf.AGB_genders, "SELECT gender_enum,gender FROM genders"
    )

    # Validate inputs
    results, error = calculator.check_inputs({}, bowstyle, gender, age, roundname)
    if error:
        return {"error": error}, 400

    # Load round
    round_obj, _, round_location, round_body = calculator.load_round(
        roundname, bowstyle
    )

    # Validate score
    results, error = calculator.check_max_score(
        round_obj, roundname, score, results
    )
    if error:
        return {"error": error}, 400

    # Calculate handicap
    hc_scheme = hc.handicap_scheme(scheme)
    hc_from_score = hc_scheme.handicap_from_score(
        float(score), round_obj, arw_d=diameter, int_prec=True
    )

    # Calculate classification using shared function
    classification_result = utils.calculate_classification(
        float(score), round_obj, round_location, round_body,
        bowstyle, gender, age,
        bowstyle_mapping[bowstyle], gender_mapping[gender], age_mapping[age],
    )

    response = {
        "bowstyle": bowstyle,
        "gender": gender,
        "roundname": roundname,
        "classification": classification_result.classification,
        "handicap": hc_from_score,
        "score": int(score),
    }

    if decimal_hc:
        response["decimal_handicap"] = hc_scheme.handicap_from_score(
            float(score), round_obj, arw_d=diameter, int_prec=False
        )

    response["warnings"] = classification_result.warnings

    return response, 200


@bp.route("/handicap", methods=("GET", "POST"))
def handicap():
    """
    Calculate handicap and classification for a given score.

    Accepts data via GET URL parameters or POST JSON body.

    Parameters
    ----------
    bowstyle, gender, age, roundname, score (required)
    decimalHC, diameter, scheme (optional)

    Returns
    -------
    JSON response containing handicap, classification, and warnings.
    """
    if request.method == "POST" and request.is_json:
        data = request.get_json()
    else:
        data = request.args

    parsed, status = parse_input(data)
    if status != 200:
        return jsonify({"error": parsed}), 400

    response, status = calc_single(parsed)
    return jsonify(response), status
