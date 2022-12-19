import os

from flask import Flask
from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from wtforms import Form, validators, SearchField, IntegerField
from . import db


class HCForm(Form):
    bowstyle = SearchField("Bowstyle", [validators.InputRequired("Please provide.")])
    gender = SearchField(
        "Gender under AGB", [validators.InputRequired("Please provide.")]
    )
    age = SearchField("Age category", [validators.InputRequired("Please provide.")])
    roundname = SearchField("Round", [validators.InputRequired("Please provide.")])
    score = IntegerField("Score", [validators.InputRequired("Please provide.")])


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
        bowstyles = database.execute(
            "SELECT bowstyle,disciplines FROM bowstyles"
        ).fetchall()
        genders = database.execute(
            "SELECT gender FROM genders"
        ).fetchall()
        ages = database.execute(
            "SELECT age_group FROM ages"
        ).fetchall()

        form = HCForm(request.form)
        if request.method == "POST" and form.validate():
            return render_template("calculate.html", form=form, bowstyles=bowstyles, genders=genders, ages=ages)
        return render_template("home.html", form=form, bowstyles=bowstyles, genders=genders, ages=ages)

    ## a simple page that says hello
    #    @app.route('/hello')
    #    def hello():
    #        return 'Hello, World!'

    db.init_app(app)

    return app
