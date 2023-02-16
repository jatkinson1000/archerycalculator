from flask import (
    Blueprint,
    render_template,
    request,
)
import numpy as np

from archerycalculator.db import query_db, sql_to_dol

from archeryutils import load_rounds
from archeryutils.handicaps import handicap_equations as hc_eq
from archeryutils.handicaps import handicap_functions as hc_func

from archerycalculator import ExtrasForm, utils

bp = Blueprint("extras", __name__, url_prefix="/extras")


@bp.route("/groups", methods=("GET", "POST"))
def groups():

    # Load form and set defaults
    form = ExtrasForm.GroupForm(
        request.form,
    )

    # Set form choices
    form.known_group_unit.choices = ["cm", "inches"]
    form.known_dist_unit.choices = ["metres", "yards"]

    error = None
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

        # Generate the handicap params
        hc_params = hc_eq.HcParams()
        hc_scheme = "AGB"

        # Calculate the handicap
        known_sig_r = known_group_size * group_scale_factor / 2.0

        def f_root(h, scheme, distance, hc_params):
            val = hc_eq.sigma_r(h, scheme, distance, hc_params)
            return val - known_sig_r

        # Rootfind value of sigma_r
        handicap = utils.rootfinding(
            -75, 300, f_root, hc_scheme, known_dist * dist_scale_factor, hc_params
        )

        # Map to other distances
        sig_r = hc_eq.sigma_r(handicap, hc_scheme, dists * dist_scale_factor, hc_params)

        # Calculate group sizes
        groups = 2.0 * sig_r

        icons = [None] * len(groups)
        for i, group in enumerate(groups):
            icons[i] = utils.group_icons(group)

        results = dict(zip(dists, zip(groups / group_scale_factor, icons)))
        print(results)

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

    # Load form and set defaults
    form = ExtrasForm.RoundComparisonForm(
        request.form,
    )

    roundnames = sql_to_dol(query_db("SELECT code_name,round_name FROM rounds"))
    roundnames = utils.indoor_display_filter(
        dict(zip(roundnames["code_name"], roundnames["round_name"]))
    )

    form.roundname.choices = [""] + roundnames

    error = None
    if request.method == "POST" and form.validate():

        # Get essential form results
        score = request.form["score"]
        roundname = request.form["roundname"]
        compound = False
        if request.form.getlist("compound"):
            compound = True

        use_rounds = {}
        if request.form.getlist("outdoor"):
            outdoor_rounds = sql_to_dol(
                query_db(
                    "SELECT code_name,round_name FROM rounds WHERE location IN ('outdoor') AND body in ('AGB','WA')"
                )
            )
            use_rounds["Outdoor Target"] = outdoor_rounds

        if request.form.getlist("indoor"):
            indoor_rounds = sql_to_dol(
                query_db(
                    "SELECT code_name,round_name FROM rounds WHERE location IN ('indoor') AND body in ('AGB','WA')"
                )
            )
            # Deal with compound
            roundsdicts = dict(
                zip(indoor_rounds["code_name"], indoor_rounds["round_name"])
            )
            noncompoundroundnames = utils.indoor_display_filter(roundsdicts)
            codenames = [
                key
                for key in list(roundsdicts.keys())
                if roundsdicts[key] in noncompoundroundnames
            ]
            if compound:
                codenames = utils.get_compound_codename(codenames)
            indoor_rounds = {
                "code_name": codenames,
                "round_name": noncompoundroundnames,
            }
            use_rounds["Indoor Target"] = indoor_rounds

        if request.form.getlist("wafield"):
            wafield_rounds = sql_to_dol(
                query_db(
                    "SELECT code_name,round_name FROM rounds WHERE location IN ('field') AND body in ('AGB','WA')"
                )
            )
            use_rounds["WA Field"] = wafield_rounds

        if request.form.getlist("ifaafield"):
            ifaafield_rounds = sql_to_dol(
                query_db(
                    "SELECT code_name,round_name FROM rounds WHERE location IN ('field') AND body in ('IFAA')"
                )
            )
            use_rounds["IFAA Field"] = ifaafield_rounds

        if request.form.getlist("virounds"):
            vi_rounds = sql_to_dol(
                query_db(
                    "SELECT code_name,round_name FROM rounds WHERE body in ('AGB-VI','WA-VI')"
                )
            )
            use_rounds["VI"] = vi_rounds

        if request.form.getlist("unofficial"):
            unofficial_rounds = sql_to_dol(
                query_db(
                    "SELECT code_name,round_name FROM rounds WHERE body IN ('custom')"
                )
            )
            use_rounds["Unofficial"] = unofficial_rounds

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
                    "Custom.json",
                ]
            )
            # Get the appropriate round from the database
            round_db_info = query_db(
                "SELECT * FROM rounds WHERE round_name IS (?)",
                [roundname],
                one=True,
            )
            if round_db_info is None:
                error = f"Invalid round name '{roundname}'. Please start typing and select from dropdown."
            else:
                round_codename = round_db_info["code_name"]

                # Check if we need compound scoring
                if compound:
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

                # Generate the handicap params
                hc_params = hc_eq.HcParams()

                if error is None:
                    # Calculate the handicap
                    hc_from_score = hc_func.handicap_from_score(
                        float(score),
                        round_obj,
                        "AGB",
                        hc_params,
                        int_prec=False,
                    )

                    results = {}
                    for item in use_rounds:
                        results_i = np.zeros(len(use_rounds[item]["code_name"]))
                        for i, round_i in enumerate(use_rounds[item]["code_name"]):
                            # Don't round up to avoid conflicts where score is different to that input
                            results_i[i] = hc_eq.score_for_round(
                                all_rounds_objs[round_i],
                                hc_from_score,
                                "AGB",
                                hc_params,
                                round_score_up=False,
                            )[0]
                        results[item] = dict(
                            zip(use_rounds[item]["round_name"], results_i)
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
