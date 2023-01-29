from flask import (
    Blueprint,
    render_template,
    request,
)
import numpy as np

from archerycalculator.db import query_db, sql_to_dol

from archeryutils import rounds
from archeryutils.handicaps import handicap_equations as hc_eq
from archeryutils.classifications import classifications as class_func

from archerycalculator import TableForm, utils

bp = Blueprint("tables", __name__, url_prefix="/tables")


@bp.route("/handicap", methods=("GET", "POST"))
def handicap_tables():

    form = TableForm.HandicapTableForm(request.form)

    roundnames = sql_to_dol(query_db("SELECT code_name,round_name FROM rounds"))
    all_rounds = utils.indoor_display_filter(
        dict(zip(roundnames["code_name"], roundnames["round_name"]))
    )

    # Set defaults
    form.round1.choices = [""] + all_rounds
    form.round2.choices = [""] + all_rounds
    form.round3.choices = [""] + all_rounds
    form.round4.choices = [""] + all_rounds
    form.round5.choices = [""] + all_rounds
    form.round6.choices = [""] + all_rounds
    form.round7.choices = [""] + all_rounds

    if request.method == "POST" and form.validate():
        error = None

        all_rounds_objs = rounds.read_json_to_round_dict(
            [
                "AGB_outdoor_imperial.json",
                "AGB_outdoor_metric.json",
                "AGB_indoor.json",
                "WA_outdoor.json",
                "WA_indoor.json",
                "WA_field.json",
                "IFAA_field.json",
                "Custom.json",
            ]
        )

        # Get form results
        rounds_req = []
        rounds_comp = []
        for i in range(7):
            if request.form[f"round{i+1}"]:
                rounds_req.append(request.form[f"round{i+1}"])
                if request.form.getlist(f"round{i+1}_compound"):
                    rounds_comp.append(True)
                else:
                    rounds_comp.append(False)

        allowance_table = False
        if request.form.getlist("allowance"):
            allowance_table = True

        round_objs = []
        for (round_i, comp_i) in zip(rounds_req, rounds_comp):
            round_query = query_db(
                "SELECT code_name FROM rounds WHERE round_name IS (?)",
                [round_i],
                one=True,
            )
            if round_query is None:
                error = f"Invalid round name '{round_i}'. Please start typing and select from dropdown."
                # If errors reload default with error message
                return render_template(
                    "handicap_tables.html",
                    form=form,
                    error=error,
                )
            else:
                round_codename = round_query["code_name"]

            # Check if we need compound scoring
            if comp_i:
                round_codename = utils.get_compound_codename(round_codename)

            # Get the appropriate rounds from the database
            round_objs.append(all_rounds_objs[round_codename])

        # Generate the handicap params
        hc_params = hc_eq.HcParams()

        results = np.zeros([151, len(round_objs) + 1])
        results[:, 0] = np.arange(0, 151).astype(np.int32)
        for i, round_obj_i in enumerate(round_objs):
            results[:, i + 1] = hc_eq.score_for_round(
                round_obj_i, results[:, 0], "AGB", hc_params
            )[0].astype(np.int32)

        if allowance_table:
            results[:, 1:] = 1440 - results[:, 1:]
        else:
            # Clean gaps where there are multiple HC for one score
            # TODO: This assumes scores are running highest to lowest.
            #  AA and AA2 will only work if hcs passed in reverse order (large to small)
            # TODO: setting fill to -9999 is a bit hacky to get around jinja interpreting
            #  0, NaN, and None as the same thing. Consider finding better solution.
            for irow, row in enumerate(results[:-1, 1:]):
                for jscore, score in enumerate(row):
                    if results[irow, jscore + 1] == results[irow + 1, jscore + 1]:
                        results[irow, jscore + 1] = -9999

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


@bp.route("/classification", methods=("GET", "POST"))
def classification_tables():

    bowstylelist = sql_to_dol(query_db("SELECT bowstyle,disciplines FROM bowstyles"))[
        "bowstyle"
    ]
    genderlist = sql_to_dol(query_db("SELECT gender FROM genders"))["gender"]
    agelist = sql_to_dol(query_db("SELECT age_group FROM ages"))["age_group"]
    classlist = sql_to_dol(query_db("SELECT shortname FROM classes"))["shortname"]

    # Load form and set defaults
    form = TableForm.ClassificationTableForm(
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
            use_rounds = sql_to_dol(
                query_db(
                    "SELECT code_name,round_name FROM rounds WHERE location IN ('outdoor') AND body in ('AGB','WA')"
                )
            )

            if bowstyle.lower() in ["traditional", "flatbow"]:
                bowstyle = "barebow"

            # Perform filtering based upon category to make more aesthetic and avoid duplicates
            roundsdicts = dict(zip(use_rounds["code_name"], use_rounds["round_name"]))
            filtered_names = utils.check_blacklist(
                use_rounds["code_name"], age, gender, bowstyle
            )
            round_names = [
                roundsdicts[key]
                for key in list(roundsdicts.keys())
                if key in filtered_names
            ]
            use_rounds = {"code_name": filtered_names, "round_name": round_names}

            results = np.zeros([len(use_rounds["code_name"]), len(classlist) - 1])
            for i, round_i in enumerate(use_rounds["code_name"]):
                results[i, :] = np.asarray(
                    class_func.AGB_outdoor_classification_scores(
                        round_i, bowstyle, gender, age
                    )
                )
        elif discipline in ["indoor"]:
            # TODO: This is a bodge - put indoor classes in database properly and fetch above!
            classlist = ["A", "B", "C", "D", "E", "F", "G", "H", "UC"]

            use_rounds = sql_to_dol(
                query_db(
                    "SELECT code_name,round_name FROM rounds WHERE location IN ('indoor') AND body in ('AGB','WA')"
                )
            )
            # Filter out compound rounds for non-recurve and vice versa
            # TODO: This is pretty horrible... is there a better way?
            roundsdicts = dict(zip(use_rounds["code_name"], use_rounds["round_name"]))
            noncompoundroundnames = utils.indoor_display_filter(roundsdicts)
            codenames = [
                key
                for key in list(roundsdicts.keys())
                if roundsdicts[key] in noncompoundroundnames
            ]
            if bowstyle.lower() in ["compound"]:
                codenames = utils.get_compound_codename(codenames)
            use_rounds = {"code_name": codenames, "round_name": noncompoundroundnames}

            results = np.zeros([len(use_rounds["code_name"]), len(classlist) - 1])
            for i, round_i in enumerate(use_rounds["code_name"]):
                results[i, :] = np.asarray(
                    class_func.AGB_indoor_classification_scores(
                        round_i, bowstyle, gender, age
                    )
                )
        elif discipline in ["field"]:
            # TODO: This is a bodge - put field classes in database properly and fetch above!
            classlist = ["GMB", "MB", "B", "1", "2", "3", "UC"]

            if bowstyle.lower() in ["recurve", "compound"]:
                use_rounds = {
                    "code_name": ["wa_field_24_red"],
                    "round_name": ["WA Field 24 Red"],
                }
            elif bowstyle.lower() in ["barebow", "longbow", "traditional", "flatbow"]:
                use_rounds = {
                    "code_name": ["wa_field_24_blue"],
                    "round_name": ["WA Field 24 Blue"],
                }

            results = np.zeros([len(use_rounds["code_name"]), len(classlist) - 1])
            for i, round_i in enumerate(use_rounds["code_name"]):
                results[i, :] = np.asarray(
                    class_func.AGB_field_classification_scores(
                        round_i, bowstyle, gender, age
                    )
                )
        else:
            # Should never get here... placeholder for field...
            # use_rounds = sql_to_dol(query_db("SELECT code_name FROM rounds WHERE location IN ('field') AND body in ('AGB','WA')"))
            # results = np.zeros([len(use_rounds["codename"]), len(classlist) - 1])
            # for i, round_i in enumerate(use_rounds["codename"]):
            #     results[i, :] = np.asarray(
            #         class_func.AGB_field_classification_scores(
            #             round_i, bowstyle, gender, age
            #         )
            pass

        # Add roundnames on to the end then flip for printing
        roundnames = [round_i for round_i in use_rounds["round_name"]]
        results = np.flip(
            np.concatenate(
                (results.astype(int), np.asarray(roundnames)[:, None]), axis=1
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
        else:
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

    roundfamilies = {
        "WA 1440/Metrics": ["wa1440", "metric1440"],
        "WA 720/Metrics": ["wa720", "metric720"],
        "York/Hereford/Bristols": ["york_hereford_bristol"],
        "St. George/Albion/Windsor": ["stgeorge_albion_windsor"],
        "National": ["national"],
        "Western": ["western"],
        "Warwick": ["warwick"],
        "WA Field 24": ["wafield_24"],
    }

    bowstylelist = sql_to_dol(query_db("SELECT bowstyle,disciplines FROM bowstyles"))[
        "bowstyle"
    ]

    # Load form and set defaults
    form = TableForm.EventTableForm(request.form, bowstyle=bowstylelist[1])
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
            and roundfamily in list(roundfamilies.keys())[3:7]
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
        if roundfamily in list(roundfamilies.keys())[:7]:
            all_rounds_objs = rounds.read_json_to_round_dict(
                [
                    "AGB_outdoor_imperial.json",
                    "AGB_outdoor_metric.json",
                    "WA_outdoor.json",
                ]
            )
            if bowstyle.lower() in ["traditional", "flatbow"]:
                bowstyle = "barebow"

            genderlist = sql_to_dol(query_db("SELECT gender FROM genders"))["gender"]
            agelist = sql_to_dol(
                query_db("SELECT age_group,male_dist,female_dist FROM ages")
            )
            classlist = sql_to_dol(query_db("SELECT shortname FROM classes"))[
                "shortname"
            ]

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
                        if all_rounds_objs[rnd_i].max_distance() >= min(
                            max_dist, int(agelist[f"{gender.lower()}_dist"][j])
                        ):
                            age_round = roundslist["code_name"][i]

                    # Check for 720 based on bowstyle
                    if roundfamily in list(roundfamilies.keys())[1]:
                        if bowstyle.lower() in ["compound"]:
                            age_round = age_round.replace("122", "80")
                            age_round = age_round.replace("70", "50_c")
                            age_round = age_round.replace("60", "50_c")
                        else:
                            age_round = age_round.replace("80", "122")
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
                        for i in class_func.AGB_outdoor_classification_scores(
                            age_round, bowstyle, gender, age_j
                        )[-1::-1]
                    ]
            classes = classlist[-2::-1]

        # Field:
        elif roundfamily in list(roundfamilies.keys())[7]:
            all_rounds_objs = rounds.read_json_to_round_dict(
                [
                    "WA_field.json",
                ]
            )

            # Done manually for now, update in future
            genderlist = sql_to_dol(query_db("SELECT gender FROM genders"))["gender"]
            agelist = {
                "age_group": ["Adult", "Under 18"],
                "male_dist": [60, 60],
                "female_dist": [60, 60],
            }
            classlist = ["GMB", "MB", "B", "1", "2", "3", "UC"]

            if bowstyle.lower() in ["barebow", "longbow", "traditional", "flatbow"]:
                agelist["male_dist"] = [50, 50]
                agelist["female_dist"] = [50, 50]

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
                        if all_rounds_objs[rnd_i].max_distance() >= int(
                            agelist[f"{gender.lower()}_dist"][j]
                        ):
                            age_round = roundslist["code_name"][i]
                    # Ensure we have the 24 target round, not 12 target unit
                    age_round = age_round.replace("12", "24")

                    results[f"{age_j} {gender}"] = [
                        sql_to_dol(
                            query_db(
                                "SELECT round_name FROM rounds WHERE code_name IN (?)",
                                [age_round],
                            )
                        )["round_name"][0]
                    ] + [
                        str(int(i))
                        for i in class_func.AGB_field_classification_scores(
                            age_round, bowstyle, gender, age_j
                        )[-1::-1]
                    ]
            classes = classlist[-2::-1]

        if error is None:
            # Return the results
            # Flip array so lowest class on left for printing
            return render_template(
                "event_tables.html",
                form=form,
                results=results,
                classes=classes,
            )
        else:
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
