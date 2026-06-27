"""API endpoint for handicap calculation."""

from flask import Blueprint, jsonify, request

from archeryutils import classifications as cf
from archeryutils import handicaps as hc
from archeryutils import load_rounds

from archerycalculator import utils
from archerycalculator.db import generate_enum_mapping

bp = Blueprint("api", __name__, url_prefix="/api")

VALID_SCHEMES = ("AGB", "AGBold", "AA", "AA2")

ROUND_SETS = [
    "AGB_outdoor_imperial.json",
    "AGB_outdoor_metric.json",
    "AGB_indoor.json",
    "WA_outdoor.json",
    "WA_indoor.json",
    "WA_field.json",
    "WA_experimental.json",
    "IFAA_field.json",
    "AGB_VI.json",
    "WA_VI.json",
    "Miscellaneous.json",
]


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
    roundcode = data.get("roundcode")
    score = data.get("score")

    missing = [
        field
        for field in ("bowstyle", "gender", "age", "roundcode", "score")
        if data.get(field) is None
    ]
    if missing:
        return f"Missing required parameters: {', '.join(missing)}", 400

    scheme = data.get("scheme", "AGB")
    if scheme not in VALID_SCHEMES:
        return f"Invalid handicap scheme. Must be one of: {', '.join(VALID_SCHEMES)}", 400

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
        "roundcode": roundcode,
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
        bowstyle, gender, age, roundcode, score, scheme, decimal_hc, diameter
    ) = (
        input_data["bowstyle"],
        input_data["gender"],
        input_data["age"],
        input_data["roundcode"],
        input_data["score"],
        input_data["scheme"],
        input_data["decimal_hc"],
        input_data["diameter"],
    )

    # Load round sets and resolve codename
    all_rounds = load_rounds.read_json_to_round_dict(ROUND_SETS)

    # Check compound variant
    if bowstyle.lower() == "compound":
        roundcode = utils.get_compound_codename(roundcode)
        if roundcode not in all_rounds:
            return {"error": f"Compound variant '{roundcode}' not found."}, 400

    if roundcode not in all_rounds:
        return {"error": f"Unknown roundcode '{roundcode}'."}, 400

    round_obj = all_rounds[roundcode]

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

    # Validate score
    max_score = round_obj.max_score()
    if int(score) <= 0:
        return {"error": "A score of 0 or less is not valid."}, 400
    elif int(score) > max_score:
        return {
            "error": (
                f"{score} is larger than the maximum possible "
                f"score of {int(max_score)} for a {round_obj.name}."
            )
        }, 400

    # Calculate handicap
    hc_scheme = hc.handicap_scheme(scheme)
    hc_from_score = hc_scheme.handicap_from_score(
        float(score), round_obj, arw_d=diameter, int_prec=True
    )

    # Calculate classification using shared function
    classification_result = utils.calculate_classification(
        float(score), round_obj, round_obj.location, round_obj.body,
        bowstyle, gender, age,
        bowstyle_mapping[bowstyle], gender_mapping[gender], age_mapping[age],
    )

    response = {
        "bowstyle": bowstyle,
        "gender": gender,
        "roundcode": round_obj.codename,
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

    Auto-detects single vs batch mode based on input type:
      - GET with URL parameters  -> single request
      - POST JSON object          -> single request
      - POST JSON array           -> batch request

    Parameters (single)
    -------------------
    bowstyle, gender, age, roundcode, score (required)
    decimalHC, diameter, scheme (optional)

    Returns
    -------
    Single request: JSON with handicap, classification, and warnings.
    Batch request: JSON array of results matching input order.
    """
    # --- extract raw input ---
    if request.method == "POST":
        if not request.is_json:
            return jsonify({"error": "POST requires JSON body"}), 400
        data = request.get_json()
    else:
        # GET -> convert ImmutableMultiDict to a plain dict
        data = {k: v for k, v in request.args.items()}

    # --- dispatch: array = batch, object = single ---
    if isinstance(data, list):
        # Batch mode
        outputs = []
        for item in data:
            parsed, status = parse_input(item)
            if status != 200:
                outputs.append({"error": parsed})
            else:
                response, _ = calc_single(parsed)
                outputs.append(response)
        return jsonify(outputs), 200

    # Single mode
    parsed, status = parse_input(data)
    if status != 200:
        return jsonify({"error": parsed}), 400

    response, status = calc_single(parsed)
    return jsonify(response), status
