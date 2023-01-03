import os

from flask import Flask
from flask import (
    # Blueprint,
    # flash,
    # g,
    # redirect,
    render_template,
    request,
    # session,
    # url_for,
)

from archeryutils import rounds
from archeryutils.handicaps import handicap_equations as hc_eq
from archeryutils.handicaps import handicap_functions as hc_func
from archeryutils.classifications import classifications as class_func

from flaskr import db
from flaskr import HCForm


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Single home page (for now)
    @app.route("/", methods=["GET", "POST"])
    def home():

        database = db.get_db()

        all_bowstyles = database.execute(
            "SELECT bowstyle,disciplines FROM bowstyles"
        ).fetchall()
        all_genders = database.execute("SELECT gender FROM genders").fetchall()
        all_ages = database.execute("SELECT age_group FROM ages").fetchall()
        all_rounds = database.execute("SELECT round_name FROM rounds").fetchall()

        bowstyle = ""
        gender = ""
        age = ""
        roundname = ""
        score = 0

        form = HCForm.HCForm(request.form)

        if request.method == "POST" and form.validate():
            error = None
            bowstyle = request.form["bowstyle"]
            gender = request.form["gender"]
            age = request.form["age"]
            roundname = request.form["roundname"]
            bowstyle = request.form["bowstyle"]
            score = request.form["score"]

            # Check the inputs are all valid
            bowstylecheck = database.execute(
                "SELECT id FROM bowstyles WHERE bowstyle IS (?)", [bowstyle]
            ).fetchall()
            if len(bowstylecheck) == 0:
                error = "Invalid bowstyle. Please select from dropdown."
            gendercheck = database.execute(
                "SELECT id FROM genders WHERE gender IS (?)", [gender]
            ).fetchall()
            if len(gendercheck) == 0:
                error = "Please select gender from dropdown options."
            agecheck = database.execute(
                "SELECT id FROM ages WHERE age_group IS (?)", [age]
            ).fetchall()
            if len(agecheck) == 0:
                error = "Invalid age group. Please select from dropdown."
            roundcheck = database.execute(
                "SELECT id FROM rounds WHERE round_name IS (?)", [roundname]
            ).fetchall()
            if len(roundcheck) == 0:
                error = "Invalid round name. Please select from dropdown."

            all_rounds_objs = rounds.read_json_to_round_dict(
                [
                    "AGB_outdoor_imperial.json",
                    "AGB_outdoor_metric.json",
                    # "AGB_indoor.json",
                    "WA_outdoor.json",
                    # "WA_indoor.json",
                    # "Custom.json",
                ]
            )
            # Get the appropriate round from the database
            round_codename = database.execute(
                "SELECT code_name FROM rounds WHERE round_name IS (?)", [roundname]
            ).fetchone()["code_name"]
            round_obj = all_rounds_objs[round_codename]

            # Generate the handicap params
            hc_params = hc_eq.HcParams()
            scheme = "AGB"

            # Check score against maximum score and return error if inappropriate
            max_score = round_obj.max_score()
            if int(score) < 0:
                error = "A score less than 0 is not valid."
            elif int(score) > max_score:
                error = (
                    f"{score} is larger than the maximum possible "
                    f"score of {int(max_score)} for a {roundname}."
                )

            if error is None:
                # Calculate the handicap
                hc_from_score = hc_func.handicap_from_score(
                    float(score), round_obj, scheme, hc_params, int_prec=True
                )
                RAD2DEG = 57.295779513
                sig_t = hc_eq.sigma_t(hc_from_score, scheme, 0.0, hc_params)
                sig_r_18 = hc_eq.sigma_r(hc_from_score, scheme, 18.0, hc_params)
                sig_r_50 = hc_eq.sigma_r(hc_from_score, scheme, 50.0, hc_params)
                sig_r_70 = hc_eq.sigma_r(hc_from_score, scheme, 70.0, hc_params)
                # Calculate the classification
                class_from_score = class_func.calculate_AGB_outdoor_classification(
                    round_codename,
                    float(score),
                    bowstyle.lower(),
                    gender.lower(),
                    age.lower(),
                )
                class_from_score = database.execute(
                    "SELECT longname FROM classes WHERE shortname IS (?)",
                    [class_from_score],
                ).fetchone()["longname"]

                # Perform calculations and return the results
                return render_template(
                    "calculate.html",
                    form=form,
                    bowstyles=all_bowstyles,
                    genders=all_genders,
                    ages=all_ages,
                    rounds=all_rounds,
                    bowstyle=bowstyle,
                    gender=gender,
                    age=age,
                    roundname=roundname,
                    score=score,
                    maxscore=int(max_score),
                    handicap=hc_from_score,
                    classification=class_from_score,
                    sig_t=2.0*RAD2DEG*sig_t,
                    sig_r_18=2.0*100.0*sig_r_18,
                    sig_r_50=2.0*100.0*sig_r_50,
                    sig_r_70=2.0*100.0*sig_r_70,
                )
            else:
                # If errors reload default
                return render_template(
                    "home.html",
                    form=form,
                    bowstyles=all_bowstyles,
                    genders=all_genders,
                    ages=all_ages,
                    rounds=all_rounds,
                    error=error,
                    # bowstyle=bowstyle,
                    # gender=gender,
                    # age=age,
                    # roundname=roundname,
                    # score=score,
                )

        # If first visit load the default form with no inputs
        return render_template(
            "home.html",
            form=form,
            bowstyles=all_bowstyles,
            genders=all_genders,
            ages=all_ages,
            rounds=all_rounds,
            error=None,
            # bowstyle=bowstyle,
            # gender=gender,
            # age=age,
            # roundname=roundname,
            # score=score,
        )

    # A simple page that says hello
    # @app.route('/hello')
    # def hello():
    #     return 'Hello, World!'

    # A simple page that says hello
    @app.route('/rounds')
    def rounds_page():
        return render_template("rounds.html",
                               rounds=[],
                               error=None)

    db.init_app(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
