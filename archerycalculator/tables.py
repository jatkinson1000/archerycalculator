"""Generate table pages on archerycalculator."""

import numpy as np
from archeryutils import classifications as class_func
from archeryutils import handicaps as hc
from archeryutils import load_rounds
from flask import (
    Blueprint,
    render_template,
    request,
)

from archerycalculator import table_form, utils
from archerycalculator.db import query_db, sql_to_dol

bp = Blueprint("tables", __name__, url_prefix="/tables")


@bp.route("/handicap", methods=("GET", "POST"))
def handicap_tables():
    """
    Generate the handicap table page in the flask app.

    Returns
    -------
    html template :
        template for the handicap table page

    """
    form = table_form.HandicapTableForm(request.form)

    roundnames = sql_to_dol(query_db("SELECT code_name,round_name FROM rounds"))
    all_rounds = utils.indoor_display_filter(
        dict(zip(roundnames["code_name"], roundnames["round_name"]))
    )

    # Set defaults
    all_rounds_list = ["", *all_rounds]
    form.round1.choices = all_rounds_list
    form.round2.choices = all_rounds_list
    form.round3.choices = all_rounds_list
    form.round4.choices = all_rounds_list
    form.round5.choices = all_rounds_list
    form.round6.choices = all_rounds_list
    form.round7.choices = all_rounds_list

    if request.method == "POST" and form.validate():
        error = None

        all_rounds_objs = load_rounds.read_json_to_round_dict(
            [
                "AGB_outdoor_imperial.json",
                "AGB_outdoor_metric.json",
                "AGB_indoor.json",
                "WA_outdoor.json",
                "WA_indoor.json",
                "WA_field.json",
                "IFAA_field.json",
                "Miscellaneous.json",
            ]
        )

        rounds_req, rounds_comp, allowance_table = get_hc_rounds(request.form)

        round_objs = []
        for round_i, comp_i in zip(rounds_req, rounds_comp):
            round_query = query_db(
                "SELECT code_name FROM rounds WHERE round_name IS (?)",
                [round_i],
                one=True,
            )
            if round_query is None:
                error = (
                    f"Invalid round name '{round_i}'. "
                    "Please start typing and select from dropdown."
                )
                # If errors reload default with error message
                return render_template(
                    "handicap_tables.html",
                    form=form,
                    error=error,
                )
            round_codename = round_query["code_name"]

            # Check if we need compound scoring
            if comp_i:
                round_codename = utils.get_compound_codename(round_codename)

            # Get the appropriate rounds from the database
            round_objs.append(all_rounds_objs[round_codename])

        # Generate numerical table of results
        results = generate_hc_table(round_objs, allowance_table)

        # Return the results
        return render_template(
            "handicap_tables.html",
            form=form,
            roundnames=rounds_req,
            results=results,
        )

    # If first visit load the default form with no inputs
    return render_template(
        "handicap_tables.html",
        form=form,
        error=None,
    )


def get_hc_rounds(web_form):
    """
    Get the rounds requested from the web form.

    Parameters
    ----------
    web_form : flask.request.form
        request from the form with results

    Returns
    -------
    rounds_req : List[str]
        rounds for which to generate handicap table
    rounds_comp : List[bool]
        use compound scoring for round in rounds_req?
    allowance_table : bool
        generate table of allowances?
    """
    # Get form results
    rounds_req = []
    rounds_comp = []
    allowance_table = False

    for i in range(7):
        if web_form[f"round{i+1}"]:
            rounds_req.append(web_form[f"round{i+1}"])
            if web_form.getlist(f"round{i+1}_compound"):
                rounds_comp.append(True)
            else:
                rounds_comp.append(False)

    if web_form.getlist("allowance"):
        allowance_table = True

    return rounds_req, rounds_comp, allowance_table


def generate_hc_table(round_objs, allowance_table):
    """
    Generate the handicap table.

    Parameters
    ----------
    round_objs : List[Round]
        list of Round objects for the rounds in the table
    allowance_table : bool
        generate table of allowances?

    Returns
    -------
    results : np.ndarray
        array with numerical values for the handicap table
    """
    results = np.zeros([151, len(round_objs) + 1])
    results[:, 0] = np.arange(0, 151).astype(np.int32)
    hc_scheme = hc.handicap_scheme("AGB")

    for i, round_obj_i in enumerate(round_objs):
        results[:, i + 1] = hc_scheme.score_for_round(
            results[:, 0],
            round_obj_i,
        ).astype(np.int32)

    if allowance_table:
        results[:, 1:] = 1440 - results[:, 1:]
    else:
        # Clean gaps where there are multiple HC for one score
        # TODO: This assumes scores are running highest to lowest.
        #  AA and AA2 will only work if hcs passed in reverse order (large to small)
        # TODO: setting fill to -9999 is a bit hacky to get around jinja interpreting
        #  0, NaN, and None as the same thing. Consider finding better solution.
        for irow, row in enumerate(results[:-1, 1:]):
            for jscore in range(len(row)):
                if results[irow, jscore + 1] == results[irow + 1, jscore + 1]:
                    results[irow, jscore + 1] = -9999

    return results


@bp.route("/classification", methods=("GET", "POST"))
def classification_tables():
    """
    Generate classification tables page.

    Returns
    -------
    html template :
        template for the classification table pages

    """
    bowstylelist = sql_to_dol(query_db("SELECT bowstyle,disciplines FROM bowstyles"))[
        "bowstyle"
    ]
    genderlist = sql_to_dol(query_db("SELECT gender FROM genders"))["gender"]
    agelist = sql_to_dol(query_db("SELECT age_group FROM ages"))["age_group"]

    # Load form and set defaults
    form = table_form.ClassificationTableForm(
        request.form, bowstyle=bowstylelist[1], gender=genderlist[1], age=agelist[1]
    )
    form.bowstyle.choices = bowstylelist
    form.gender.choices = genderlist
    form.age.choices = agelist

    form.discipline.choices = [
        ("outdoor", "Target Outdoor"),
        ("indoor", "Target Indoor"),
        ("field", "Field"),
    ]

    if request.method == "POST" and form.validate():
        error = None

        # Get form results and store for return
        bowstyle = request.form["bowstyle"]
        gender = request.form["gender"]
        age = request.form["age"]
        discipline = request.form["discipline"]

        results = {}

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

        if discipline in ["outdoor"]:
            classlist = sql_to_dol(
                query_db("SELECT shortname FROM classes WHERE location IS 'outdoor'")
            )["shortname"]

            use_rounds = sql_to_dol(
                query_db(
                    "SELECT code_name,round_name,family FROM rounds "
                    "WHERE location IN ('outdoor') AND body in ('AGB','WA')"
                )
            )

            if bowstyle.lower() in ["traditional", "flatbow", "asiatic"]:
                bowstyle = "barebow"
            elif bowstyle.lower() in ["compound barebow"]:
                bowstyle = "compound"

            # Filter based on category to make more aesthetic and avoid duplicates
            roundsdicts = dict(zip(use_rounds["code_name"], use_rounds["round_name"]))

            filtered_names = utils.check_blacklist(
                use_rounds["code_name"], age, gender, bowstyle
            )

            # Sort filtered rounds into the order desired for outputting
            rounds_families = {
                codename: family
                for (codename, family) in dict(
                    zip(use_rounds["code_name"], use_rounds["family"])
                ).items()
                if codename in filtered_names
            }
            ordered_names = list(utils.order_rounds(rounds_families).keys())

            # Get list of actual names for pretty output
            # round_names = [
            #    roundsdicts[key]
            #    for key in list(roundsdicts.keys())
            #    if key in ordered_names
            # ]
            round_names = [roundsdicts[codename] for codename in ordered_names]

            # Final dict of rounds to use
            use_rounds = {"code_name": ordered_names, "round_name": round_names}

            results = np.zeros([len(use_rounds["code_name"]), len(classlist) - 1])
            for i, round_i in enumerate(use_rounds["code_name"]):
                results[i, :] = np.asarray(
                    class_func.agb_outdoor_classification_scores(
                        round_i, bowstyle, gender, age
                    )
                )

        elif discipline in ["indoor"]:
            classlist = sql_to_dol(
                query_db("SELECT shortname FROM classes WHERE location IS 'indoor'")
            )["shortname"]

            use_rounds = sql_to_dol(
                query_db(
                    "SELECT code_name,round_name FROM rounds "
                    "WHERE location IN ('indoor') AND body in ('AGB','WA')"
                )
            )

            if bowstyle.lower() in ["traditional", "flatbow", "asiatic"]:
                bowstyle = "barebow"
            elif bowstyle.lower() in ["compound barebow"]:
                bowstyle = "compound"

            roundsdicts = dict(zip(use_rounds["code_name"], use_rounds["round_name"]))

            # Filter out:
            #   - compound rounds for non-recurve and vice versa
            #   - triple spot rounds for all
            # Get rid of all compound rounds
            noncompoundroundnames = utils.indoor_display_filter(roundsdicts)
            codenames = [
                key
                for key in list(roundsdicts.keys())
                if roundsdicts[key] in noncompoundroundnames
            ]
            # Filter out triple-spot rounds using blacklist function and get
            # corresponding reduced set of 'non-compound' roundnames.
            codenames = utils.check_blacklist(codenames, age, gender, bowstyle)
            noncompoundroundnames = [roundsdicts[codename] for codename in codenames]
            # Convert codenames to compound codename if required.
            if "compound" in bowstyle.lower():
                codenames = utils.get_compound_codename(codenames)
            use_rounds = {"code_name": codenames, "round_name": noncompoundroundnames}
            results = np.zeros([len(use_rounds["code_name"]), len(classlist) - 1])
            for i, round_i in enumerate(use_rounds["code_name"]):
                results[i, :] = np.asarray(
                    class_func.agb_indoor_classification_scores(
                        round_i, bowstyle, gender, age
                    )
                )

        elif discipline in ["field"]:
            # TODO: This is a bodge - put field classes in database and fetch above!
            classlist = ["GMB", "MB", "B", "1", "2", "3", "UC"]

            if bowstyle.lower() in ["recurve", "compound"]:
                use_rounds = {
                    "code_name": [
                        "wa_field_24_red_marked",
                        "wa_field_24_red_unmarked",
                        "wa_field_24_red_mixed",
                    ],
                    "round_name": [
                        "WA Field 24 Red Marked",
                        "WA Field 24 Red Unmarked",
                        "WA Field 24 Red Mixed",
                    ],
                }
            elif bowstyle.lower() in ["barebow", "longbow", "traditional", "flatbow"]:
                use_rounds = {
                    "code_name": [
                        "wa_field_24_blue_marked",
                        "wa_field_24_blue_unmarked",
                        "wa_field_24_blue_mixed",
                    ],
                    "round_name": [
                        "WA Field 24 Blue Marked",
                        "WA Field 24 Blue Unmarked",
                        "WA Field 24 Blue Mixed",
                    ],
                }

            results = np.zeros([len(use_rounds["code_name"]), len(classlist) - 1])
            for i, round_i in enumerate(use_rounds["code_name"]):
                results[i, :] = np.asarray(
                    class_func.old_agb_field_classification_scores(
                        round_i, bowstyle, gender, age
                    )
                )



#             classlist = sql_to_dol(
#                 query_db("SELECT shortname FROM classes WHERE location IS 'outdoor'")
#             )["shortname"]
# 
#             # Handle age groups - field has no U21
#             if age.lower().replace(" ", "") in ("under21"):
#                 age = "Adult"
# 
#             use_rounds = sql_to_dol(
#                 query_db(
#                     "SELECT code_name,round_name FROM rounds WHERE location IN ('field') AND body in ('AGB','WA') AND NOT code_name LIKE '%12%'"
#                 )
#             )
# 
#             results = np.zeros([len(use_rounds["code_name"]), len(classlist) - 1])
#             for i, round_i in enumerate(use_rounds["code_name"]):
#                 results[i, :] = np.asarray(
#                     class_func.agb_field_classification_scores(
#                         round_i, bowstyle, gender, age
#                     )
#                 )

        else:
            # Should never get here... placeholder for next classification system.
            pass

        # Add roundnames on to the end and flip for printing
        results = np.flip(
            np.concatenate(
                (results.astype(int), np.asarray(use_rounds["round_name"])[:, None]),
                axis=1,
            ),
            axis=1,
        )
        classes = classlist[-2::-1]

        if error is None:
            # Return the results
            # Flip array so lowest class on left for printing
            return render_template(
                "classification_tables.html",
                form=form,
                results=results.astype(str),
                classes=classes,
            )

        # If errors reload default with error message
        return render_template(
            "classification_tables.html",
            form=form,
            error=error,
        )

    # If first visit load the default form with no inputs
    return render_template(
        "classification_tables.html",
        form=form,
        error=None,
    )


@bp.route("/classbyevent", methods=("GET", "POST"))
def event_tables():
    """
    Generate classification tables by event page.

    Returns
    -------
    html template :
        template for the classification table by event page

    """
    roundfamilies = {
        "WA 1440/Metrics": ["wa1440", "metric1440"],
        "WA 720/Metrics": ["wa720", "metric720"],
        "York/Hereford/Bristols": ["york_hereford_bristol"],
        "St. George/Albion/Windsor": ["stgeorge_albion_windsor"],
        "National": ["national"],
        "Western": ["western"],
        "Warwick": ["warwick"],
        "Portsmouth": ["portsmouth"],
        "WA 18": ["wa18"],
        "WA Field 24 Marked": ["wafield_24_marked"],
        "WA Field 24 Unmarked": ["wafield_24_unmarked"],
        "WA Field 24 Mixed": ["wafield_24_mixed"],
    }

    bowstylelist = sql_to_dol(query_db("SELECT bowstyle,disciplines FROM bowstyles"))[
        "bowstyle"
    ]

    # Load form and set defaults
    form = table_form.EventTableForm(request.form, bowstyle=bowstylelist[1])
    form.bowstyle.choices = bowstylelist

    form.roundfamily.choices = list(roundfamilies.keys())

    if request.method == "POST" and form.validate():
        error = None

        # Get form results and store for return
        bowstyle = request.form["bowstyle"]
        roundfamily = request.form["roundfamily"]

        # If restricting to named round set max dist as 60
        if (
            request.form.getlist("restrict_to_named")
            and roundfamily in list(roundfamilies)[3:7]
        ):
            max_dist = 60
        else:
            max_dist = 9999

        # Check the inputs are all valid
        bowstylecheck = query_db(
            "SELECT id FROM bowstyles WHERE bowstyle IS (?)", [bowstyle]
        )
        if len(bowstylecheck) == 0:
            error = "Invalid bowstyle. Please select from dropdown."

        # Account for nuances in each discipline and generate results
        # Target outdoor:
        if roundfamily in list(roundfamilies)[:7]:
            all_rounds_objs = load_rounds.read_json_to_round_dict(
                [
                    "AGB_outdoor_imperial.json",
                    "AGB_outdoor_metric.json",
                    "WA_outdoor.json",
                ]
            )
            if bowstyle.lower() in ["traditional", "flatbow", "asiatic"]:
                bowstyle = "barebow"
            elif bowstyle.lower() in ["compound barebow"]:
                bowstyle = "compound"

            genderlist = sql_to_dol(query_db("SELECT gender FROM genders"))["gender"]
            agelist = sql_to_dol(
                query_db("SELECT age_group,male_dist,female_dist FROM ages")
            )
            classlist = sql_to_dol(
                query_db("SELECT shortname FROM classes WHERE location IS 'outdoor'")
            )["shortname"]

            roundslist = {"code_name": [], "round_name": []}
            for family_i in roundfamilies[roundfamily]:
                roundslist_i = sql_to_dol(
                    query_db(
                        "SELECT code_name,round_name FROM rounds WHERE family IN (?)",
                        [family_i],
                    )
                )
                for k in roundslist:
                    roundslist[k] = roundslist[k] + roundslist_i[k]

            results = {}
            for gender in genderlist:
                for j, age_j in enumerate(agelist["age_group"]):
                    # Get appropriate round from distance
                    for i, rnd_i in enumerate(roundslist["code_name"]):
                        if all_rounds_objs[rnd_i].max_distance().value >= min(
                            max_dist, int(agelist[f"{gender.lower()}_dist"][j])
                        ):
                            age_round = roundslist["code_name"][i]

                    # Check for 720 based on bowstyle
                    if roundfamily in list(roundfamilies)[1]:
                        if bowstyle.lower() in ["compound"]:
                            age_round = age_round.replace("122", "80")
                            age_round = age_round.replace("70", "50_c")
                            age_round = age_round.replace("60", "50_c")
                        else:
                            age_round = age_round.replace("80", "122")
                            if age_j.lower().replace(" ", "") in ["adult", "under21"]:
                                age_round = "wa720_70"
                            elif age_j.lower().replace(" ", "") in ["50+", "under18"]:
                                age_round = age_round.replace("70", "60")
                            elif age_j.lower().replace(" ", "") in ["under16"]:
                                age_round = "metric_122_50"
                            if bowstyle.lower() in ["barebow"]:
                                age_round = age_round.replace("70", "50_b")
                                age_round = age_round.replace("60", "50_b")

                    # Check aliases
                    age_round = utils.check_alias(
                        age_round, age_j, gender, bowstyle.lower()
                    )

                    results[f"{age_j} {gender}"] = [
                        sql_to_dol(
                            query_db(
                                "SELECT round_name FROM rounds WHERE code_name IN (?)",
                                [age_round],
                            )
                        )["round_name"][0]
                    ] + [
                        str(int(i))
                        for i in class_func.agb_outdoor_classification_scores(
                            age_round, bowstyle, gender, age_j
                        )[-1::-1]
                    ]
            classes = classlist[-2::-1]

        # Target indoor:
        if roundfamily in list(roundfamilies)[7:9]:
            all_rounds_objs = load_rounds.read_json_to_round_dict(
                [
                    "AGB_indoor.json",
                    "WA_indoor.json",
                ]
            )
            if bowstyle.lower() in ["traditional", "flatbow", "asiatic"]:
                bowstyle = "barebow"
            elif bowstyle.lower() in ["compound barebow"]:
                bowstyle = "compound"

            genderlist = sql_to_dol(query_db("SELECT gender FROM genders"))["gender"]
            agelist = sql_to_dol(query_db("SELECT age_group FROM ages"))
            classlist = sql_to_dol(
                query_db("SELECT shortname FROM classes WHERE location IS 'indoor'")
            )["shortname"]

            round_codename = roundfamilies[roundfamily][0]

            results = {}
            for gender in genderlist:
                for age_j in agelist["age_group"]:
                    # Check for Compound round
                    if bowstyle.lower() in ["compound"]:
                        age_round = round_codename + "_compound"
                    else:
                        age_round = round_codename

                    results[f"{age_j} {gender}"] = [
                        sql_to_dol(
                            query_db(
                                "SELECT round_name FROM rounds WHERE code_name IN (?)",
                                [round_codename],
                            )
                        )["round_name"][0]
                    ] + [
                        str(int(i))
                        for i in class_func.agb_indoor_classification_scores(
                            age_round, bowstyle, gender, age_j
                        )[-1::-1]
                    ]
            classes = classlist[-2::-1]

        # Field:
        elif roundfamily in list(roundfamilies)[9:]:
            all_rounds_objs = load_rounds.read_json_to_round_dict(
                [
                    "WA_field.json",
                ]
            )

            # Done manually for now, update in future
            genderlist = sql_to_dol(query_db("SELECT gender FROM genders"))["gender"]
            agelist = {"age_group": ["Adult", "Under 18"], "peg": ["red", "red"]}
            classlist = ["GMB", "MB", "B", "1", "2", "3", "UC"]

            if bowstyle.lower() in ["barebow", "longbow", "traditional", "flatbow"]:
                agelist["peg"] = ["blue", "blue"]

            roundslist = {"code_name": [], "round_name": []}
            for family_i in roundfamilies[roundfamily]:
                roundslist_i = sql_to_dol(
                    query_db(
                        "SELECT code_name,round_name FROM rounds WHERE family IN (?)",
                        [family_i],
                    )
                )
                for k in roundslist:
                    roundslist[k] = roundslist[k] + roundslist_i[k]

            results = {}
            for gender in genderlist:
                for j, age_j in enumerate(agelist["age_group"]):
                    # Get appropriate round from distance
                    age_app_rounds = []
                    for rnd_i in roundslist["code_name"]:
                        if f"{agelist['peg'][j]}" in rnd_i:
                            age_app_rounds.append(rnd_i)

                    # Ensure 24 target round, not 12 target unit and remove duplicates
                    age_app_rounds = list(
                        {x.replace("12", "24") for x in age_app_rounds}
                    )

                    results[f"{age_j} {gender}"] = [
                        sql_to_dol(
                            query_db(
                                "SELECT round_name FROM rounds WHERE code_name IN (?)",
                                age_app_rounds,
                            )
                        )["round_name"][0]
                    ] + [
                        str(int(i))
                        for i in class_func.old_agb_field_classification_scores(
                            age_app_rounds[0], bowstyle, gender, age_j
                        )[-1::-1]
                    ]
            classes = classlist[-2::-1]

#             genderlist = sql_to_dol(query_db("SELECT gender FROM genders"))["gender"]
#             # Select only AGB Field age groups
#             agelist = sql_to_dol(
#                 query_db(
#                     "SELECT age_group,red_dist_min,blue_dist_min FROM ages WHERE NOT (age_group LIKE '%21%')"
#                 )
#             )
#             classlist = sql_to_dol(
#                 query_db("SELECT shortname FROM classes WHERE location IS 'outdoor'")
#             )["shortname"]
# 
#             roundslist = {"code_name": [], "round_name": []}
#             for family_i in roundfamilies[roundfamily]:
#                 roundslist_i = sql_to_dol(
#                     query_db(
#                         "SELECT code_name,round_name FROM rounds WHERE family IN (?)",
#                         [family_i],
#                     )
#                 )
#                 for k in roundslist:
#                     roundslist[k] = roundslist[k] + roundslist_i[k]
# 
#             results = {}
#             for gender in genderlist:
#                 for j, age_j in enumerate(agelist["age_group"]):
#                     # Get appropriate round from distance
#                     age_app_rounds = []
# 
#                     # Set appropriate pegs for ages/bowstyles
#                     # Use marked round for distance purposes
#                     for i, rnd_i in enumerate(roundslist["code_name"]):
#                         if bowstyle.lower() in ["compound", "recurve"]:
#                             min_dist = agelist["red_dist_min"][j]
#                         else:
#                             min_dist = agelist["blue_dist_min"][j]
#                         if all_rounds_objs[
#                             rnd_i.replace("unmarked", "marked").replace(
#                                 "mixed", "marked"
#                             )
#                         ].max_distance().value >= float(min_dist):
#                             age_app_rounds.append(rnd_i)
# 
#                     # Ensure 24 target round, not 12 target unit and remove duplicates
#                     age_app_rounds = list(
#                         {x.replace("12", "24") for x in age_app_rounds}
#                     )
#                     age_app_rounds = sorted(
#                         age_app_rounds, key=lambda x: all_rounds_objs[x].max_distance()
#                     )
# 
#                     # Use the shortest eligible round for each category
#                     results[f"{age_j} {gender}"] = [
#                         sql_to_dol(
#                             query_db(
#                                 "SELECT round_name FROM rounds WHERE code_name IN (?)",
#                                 [age_app_rounds[0]],
#                             )
#                         )["round_name"][0]
#                     ] + [
#                         str(int(i))
#                         for i in class_func.agb_field_classification_scores(
#                             age_app_rounds[0], bowstyle, gender, age_j
#                         )[-1::-1]
#                     ]
#             classes = classlist[-2::-1]

        if error is None:
            # Return the results
            # Flip array so lowest class on left for printing
            return render_template(
                "event_tables.html",
                form=form,
                results=results,
                classes=classes,
            )

        # If errors reload default with error message
        return render_template(
            "event_tables.html",
            form=form,
            error=error,
        )

    # If first visit load the default form with no inputs
    return render_template(
        "event_tables.html",
        form=form,
        error=None,
    )
