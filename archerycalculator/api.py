"""API endpoint for handicap calculation."""

from archeryutils import classifications as cf
from archeryutils import handicaps as hc
from flask import Blueprint, jsonify, request

from archerycalculator import calculator
from archerycalculator.db import generate_enum_mapping, query_db

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/handicap", methods=("GET", "POST"))
def handicap():
    """
    Calculate handicap and classification for a given score.

    Accepts data via GET URL parameters or POST JSON body.

    Parameters
    ----------
    All parameters can be provided via GET query string or POST JSON:
        bowstyle (required): e.g. "Recurve", "Compound", "Barebow"
        gender (required): e.g. "Open", "Female"
        age (required): e.g. "Adult", "50+", "Under 21"
        roundname (required): e.g. "WA 1440 70m", "720 18m"
        score (required): archer's score as integer
        decimalHC (optional): true/false for decimal handicap
        diameter (optional): custom arrow diameter in mm
        scheme (optional): handicap scheme, one of "AGB", "AGBold", "AA", "AA2"

    Returns
    -------
    JSON response containing handicap, classification, and warnings.
    """
    if request.method == "POST" and request.is_json:
        data = request.get_json()
    else:
        data = request.args

    # Required fields
    bowstyle = data.get("bowstyle")
    gender = data.get("gender")
    age = data.get("age")
    roundname = data.get("roundname")
    score = data.get("score")

    # Check required fields
    missing = [
        field
        for field in ("bowstyle", "gender", "age", "roundname", "score")
        if data.get(field) is None
    ]
    if missing:
        msg = f"Missing required parameters: {', '.join(missing)}"
        return jsonify({"error": msg}), 400

    # Optional fields
    diameter = float(data.get("diameter", 0.0)) * 1.0e-3
    scheme = data.get("scheme", "AGB")
    decimal_hc = data.get("decimalHC", False)
    if isinstance(decimal_hc, str):
        decimal_hc = decimal_hc.lower() in ("true", "1", "yes")
    if diameter == 0.0:
        diameter = None

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
        return jsonify({"error": error}), 400

    # Load round
    round_obj, _, round_location, round_body = calculator.load_round(
        roundname, bowstyle
    )

    # Validate score
    results, error = calculator.check_max_score(round_obj, roundname, score, results)
    if error:
        return jsonify({"error": error}), 400

    # Calculate handicap
    hc_scheme = hc.handicap_scheme(scheme)
    hc_from_score = hc_scheme.handicap_from_score(
        float(score), round_obj, arw_d=diameter, int_prec=True
    )

    response = {
        "bowstyle": bowstyle,
        "gender": gender,
        "age": age,
        "roundname": roundname,
        "score": int(score),
        "handicap": hc_from_score,
    }

    # Optional decimal handicap
    if decimal_hc:
        decimal_hc_value = hc_scheme.handicap_from_score(
            float(score), round_obj, arw_d=diameter, int_prec=False
        )
        response["decimal_handicap"] = decimal_hc_value

    # Warnings
    warnings = []

    # Calculate classification
    warning_bowstyle = None

    if round_location == "outdoor" and round_body in ("AGB", "WA"):
        if bowstyle.lower() in ("traditional", "flatbow", "asiatic"):
            warning_bowstyle = (
                f"Note: Treating {bowstyle} as Barebow "
                "for the purposes of classifications."
            )
        elif bowstyle.lower() in ("compound barebow", "compound limited"):
            warning_bowstyle = (
                f"Note: Treating {bowstyle} as Compound "
                "for the purposes of classifications."
            )

        class_short = cf.calculate_agb_outdoor_classification(
            float(score),
            round_obj,
            **cf.coax_outdoor_group(
                bowstyle_mapping[bowstyle],
                gender_mapping[gender],
                age_mapping[age],
            ),
        )
        class_long = query_db(
            "SELECT longname FROM classes WHERE shortname IS (?)",
            [class_short],
            one=True,
        )["longname"]
        response["classification"] = class_long

    elif round_location == "indoor" and round_body in ("AGB", "WA"):
        if bowstyle.lower() in ("traditional", "flatbow", "asiatic"):
            warning_bowstyle = (
                f"Note: Treating {bowstyle} as Barebow "
                "for the purposes of classifications."
            )
        elif bowstyle.lower() in ("compound barebow", "compound limited"):
            warning_bowstyle = (
                f"Note: Treating {bowstyle} as Compound "
                "for the purposes of classifications."
            )

        class_short = cf.calculate_agb_indoor_classification(
            float(score),
            round_obj,
            **cf.coax_indoor_group(
                bowstyle_mapping[bowstyle],
                gender_mapping[gender],
                age_mapping[age],
            ),
        )
        class_long = query_db(
            "SELECT longname FROM classes WHERE shortname IS (?)",
            [class_short],
            one=True,
        )["longname"]
        response["classification"] = class_long

    elif round_location == "field" and round_body in ("AGB", "WA"):
        class_short = cf.calculate_agb_field_classification(
            float(score),
            round_obj,
            **cf.coax_field_group(
                bowstyle_mapping[bowstyle],
                gender_mapping[gender],
                age_mapping[age],
            ),
        )
        response["classification"] = class_short
        warnings.append(
            "Note: This round is not officially recognised by "
            "Archery GB for the purposes of handicapping."
        )
    else:
        response["classification"] = "not currently available"
        warnings.append(
            "Note: This round is not officially recognised by "
            "Archery GB for the purposes of handicapping."
        )

    if warning_bowstyle:
        warnings.append(warning_bowstyle)

    # Sigma statistics (group size estimates)
    RAD2DEG = 57.295779513
    sig_t = hc_scheme.sigma_t(hc_from_score, 0.0)
    sig_r_18 = hc_scheme.sigma_r(hc_from_score, 18.0)
    sig_r_50 = hc_scheme.sigma_r(hc_from_score, 50.0)
    sig_r_70 = hc_scheme.sigma_r(hc_from_score, 70.0)

    response["sigma"] = {
        "angular_spread_deg": round(2.0 * RAD2DEG * sig_t, 4),
        "group_18m_cm": round(2.0 * 100.0 * sig_r_18, 2),
        "group_50m_cm": round(2.0 * 100.0 * sig_r_50, 2),
        "group_70m_cm": round(2.0 * 100.0 * sig_r_70, 2),
    }

    response["warnings"] = warnings

    # Reorder response fields
    ordered_response = {
        "bowstyle": response["bowstyle"],
        "gender": response["gender"],
        "age": response["age"],
        "roundname": response["roundname"],
        "score": response["score"],
        "handicap": response["handicap"],
        "classification": response["classification"],
        **({"decimal_handicap": response["decimal_handicap"]} if "decimal_handicap" in response else {}),
        "warnings": response["warnings"],
    }

    return jsonify(ordered_response)
