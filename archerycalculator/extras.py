"""Code for 'extra' functionalities on archerycalculator."""

import numpy as np
from archeryutils import handicaps as hc
from archeryutils import load_rounds
from flask import (
    Blueprint,
    render_template,
    request,
)

from archerycalculator import extras_form, utils
from archerycalculator.db import query_db, sql_to_dol

# handicap scheme info
HC_SCHEME = "AGB"

bp = Blueprint("extras", __name__, url_prefix="/extras")


@bp.route("/groups", methods=("GET", "POST"))
def groups():
    """
    Calculate comparative group sizes at different distances.

    Returns
    -------
    html template :
        call to html templating function
    """
    # Load form and set defaults
    form = extras_form.GroupForm(
        request.form,
    )

    # Set form choices
    form.known_group_unit.choices = ["cm", "inches"]
    form.known_dist_unit.choices = ["metres", "yards"]

    if request.method == "POST" and form.validate():
        # Get essential form results
        known_group_size = float(request.form["known_group_size"])
        known_group_unit = request.form["known_group_unit"]
        known_dist = float(request.form["known_dist"])
        known_dist_unit = request.form["known_dist_unit"]

        # Check the inputs are all valid
        known_group_size = abs(known_group_size)
        known_dist = abs(known_dist)

        if known_group_unit == "cm":
            group_scale_factor = 1e-2
            group_unit = "cm"
        else:
            group_scale_factor = 2.54e-2
            group_unit = "in"

        if known_dist_unit == "metres":
            dists = np.asarray([18.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 90.0])
            dist_scale_factor = 1.0
            dist_unit = "m"
        else:
            dists = np.asarray([20.0, 30.0, 40.0, 50.0, 60.0, 80.0, 100.0])
            dist_scale_factor = 0.9144
            dist_unit = "yd"

        hc_scheme = hc.handicap_scheme(HC_SCHEME)

        # Calculate the handicap
        known_sig_r = known_group_size * group_scale_factor / 2.0

        def f_root(h, scheme, distance):
            val = scheme.sigma_r(h, distance)
            return val - known_sig_r

        # Rootfind value of sigma_r
        handicap = utils.rootfinding(
            -75, 300, f_root, hc_scheme, known_dist * dist_scale_factor
        )

        # Map to other distances
        sig_r = hc_scheme.sigma_r(handicap, dists * dist_scale_factor)

        # Calculate group sizes
        groupsize = 2.0 * sig_r

        icons = [None] * len(groupsize)
        for i, group in enumerate(groupsize):
            icons[i] = utils.group_icons(group)

        results = dict(zip(dists, zip(groupsize / group_scale_factor, icons)))

        # Return the results
        return render_template(
            "groups.html",
            form=form,
            results=results,
            group_unit=group_unit,
            dist_unit=dist_unit,
        )

    # If first visit load the default form with no inputs
    return render_template(
        "groups.html",
        form=form,
        results=None,
    )


@bp.route("/roundscomparison", methods=("GET", "POST"))
def roundcomparison():
    """
    Calculate comparative scores on other rounds.

    Returns
    -------
    html template :
        call to html templating function
    """
    # Load form and set defaults
    form = extras_form.RoundComparisonForm(
        request.form,
    )

    roundnames = sql_to_dol(query_db("SELECT code_name,round_name FROM rounds"))
    roundnames = utils.indoor_display_filter(
        dict(zip(roundnames["code_name"], roundnames["round_name"]))
    )

    form.roundname.choices = ["", *roundnames]

    error = None

    # Process returned results
    if request.method == "POST" and form.validate():
        # Get essential form results
        score = request.form["score"]
        roundname = request.form["roundname"]

        # Get dict of round groups we will compare to
        use_rounds = get_rounds_dict(request.form)

        if len(use_rounds) == 0:
            error = "Please select one of more groups of rounds to compare to."
        else:
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
                    "Miscellaneous.json",
                ]
            )
            # Get the appropriate round from the database
            round_db_info = query_db(
                "SELECT * FROM rounds WHERE round_name IS (?)",
                [roundname],
                one=True,
            )
            if round_db_info is None:
                error = (
                    f"Invalid round name '{roundname}'. "
                    "Please start typing and select from dropdown."
                )
            else:
                round_codename = round_db_info["code_name"]

                # Check if we need compound scoring
                if request.form.getlist("compound"):
                    round_codename = utils.get_compound_codename(round_codename)
                round_obj = all_rounds_objs[round_codename]

                # Check score against maximum score and return error if inappropriate
                max_score = round_obj.max_score()
                if int(score) <= 0:
                    error = "A score of 0 or less is not valid."
                elif int(score) > max_score:
                    error = (
                        f"{score} is larger than the maximum possible "
                        f"score of {int(max_score)} for a {roundname}."
                    )

                hc_scheme = hc.handicap_scheme(HC_SCHEME)

                if error is None:
                    # Calculate the handicap
                    hc_from_score = hc_scheme.handicap_from_score(
                        float(score),
                        round_obj,
                        int_prec=False,
                    )

                    results = get_results_dict(
                        use_rounds, hc_from_score, all_rounds_objs
                    )
                    # Return the results
                    return render_template(
                        "roundscomparison.html",
                        form=form,
                        rounds=roundnames,
                        results=results,
                    )

    # If first visit load the default form with no inputs
    return render_template(
        "roundscomparison.html",
        form=form,
        rounds=roundnames,
        results=None,
        error=error,
    )


def get_rounds_dict(form_results):
    """
    Create a dictionary of families of rounds to compare to.

    Parameters
    ----------
    form_results :
        results from the form stating what to compare to

    Returns
    -------
    use_rounds : Dict[str : List[str]]
        Dict of lists of rounds in each family
    """
    use_rounds = {}
    if form_results.getlist("outdoor"):
        use_rounds["Outdoor Target"] = utils.fetch_and_sort_rounds(
            location="outdoor", body=["AGB", "WA"]
        )

    if form_results.getlist("indoor"):
        indoor_rounds = utils.fetch_and_sort_rounds(
            location="indoor", body=["AGB", "WA"]
        )
        # Deal with compound
        roundsdicts = dict(zip(indoor_rounds["code_name"], indoor_rounds["round_name"]))
        noncompoundroundnames = utils.indoor_display_filter(roundsdicts)
        codenames = [
            key
            for key in list(roundsdicts.keys())
            if roundsdicts[key] in noncompoundroundnames
        ]
        if request.form.getlist("compound"):
            codenames = utils.get_compound_codename(codenames)
        indoor_rounds = {
            "code_name": codenames,
            "round_name": noncompoundroundnames,
        }
        use_rounds["Indoor Target"] = indoor_rounds

    if form_results.getlist("wafield"):
        use_rounds["WA Field"] = utils.fetch_and_sort_rounds(
            location="field", body=["AGB", "WA"]
        )

    if form_results.getlist("ifaafield"):
        use_rounds["IFAA Field"] = utils.fetch_and_sort_rounds(
            location="field", body="IFAA"
        )

    # TODO These don't use a location.
    # Condiser doing so or extending fetch and sort function
    if form_results.getlist("virounds"):
        vi_rounds = sql_to_dol(
            query_db(
                "SELECT code_name,round_name "
                "FROM rounds WHERE body in ('AGB-VI','WA-VI')"
            )
        )
        use_rounds["VI"] = vi_rounds

    if request.form.getlist("unofficial"):
        unofficial_rounds = sql_to_dol(
            query_db("SELECT code_name,round_name FROM rounds WHERE body IN ('custom')")
        )
        use_rounds["Unofficial"] = unofficial_rounds

    return use_rounds


def get_results_dict(use_rounds, hc_from_score, all_rounds_objs):
    """
    Calculate scores on the rounds we want to copare to.

    Parameters
    ----------
    use_rounds : Dict[str: List[str]]
        results from the form stating what to compare to
    hc_from_score : float
        handicap from input score
    all_rounds_objs : Dict[str: Round]
        dict of roundnames and Round objects

    Returns
    -------
    results : Dict[str : Dict[str : int]]
        Dict of Dicts of scores for each round in each family
    """
    results = {}
    for roundgroup, roundset in use_rounds.items():
        results_i = np.zeros(len(roundset["code_name"]))
        for i, round_i in enumerate(roundset["code_name"]):
            # Don't round up to avoid conflicts where score is
            # different to that input
            results_i[i] = hc.score_for_round(
                hc_from_score,
                all_rounds_objs[round_i],
                HC_SCHEME,
                rounded_score=False,
            )
        results[roundgroup] = dict(zip(roundset["round_name"], results_i))
    return results
