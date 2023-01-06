import os

from flask import Flask
from flask import (
    # Blueprint,
    # flash,
    # g,
    # redirect,
    render_template,
    # request,
    # session,
    # url_for,
)

from flaskr import db


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

    # A simple page that says hello
    @app.route("/rounds")
    def rounds_page():
        return render_template("rounds.html", rounds=[], error=None)

    from flaskr import calculator

    app.register_blueprint(calculator.bp)
    # Not 100% sure next line is neccessary... TODO: investigate further
    app.add_url_rule("/", endpoint="calculator")

    db.init_app(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
