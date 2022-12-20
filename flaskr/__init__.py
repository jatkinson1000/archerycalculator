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

from archeryutils.archeryutils import (
    rounds,
    handicap_equations as hc_eq,
    handicap_functions as hc_func,
)

from . import db
from . import HCForm


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

    # TODO: separate function to pre-populate databases in other file

    # Simple home page
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
            bowstyle = request.form["bowstyle"]
            gender = request.form["gender"]
            age = request.form["age"]
            roundname = request.form["roundname"]
            bowstyle = request.form["bowstyle"]
            score = request.form["score"]

            error = None

            # Get the appropriate round from the database
            codename = database.execute(
                "SELECT code_name FROM rounds WHERE round_name IS (?)", [roundname]
            ).fetchone()["code_name"]
            round_obj = rounds.AGB_outdoor_imperial[codename]

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
            else:
                # Calculate the handicap
                hc_from_score = hc_func.handicap_from_score(
                    float(score), round_obj, scheme, hc_params, int_prec=True
                )

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
                )

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
    #    @app.route('/hello')
    #    def hello():
    #        return 'Hello, World!'

    db.init_app(app)

    return app
