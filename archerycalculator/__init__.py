"""Flask app for archerycalculator website."""
import os

from flask import Flask

from archerycalculator import db, calculator, tables, rounds, info, about, extras


def create_app(test_config=None):
    """
    Create and initialise the main application.

    Parameters
    ----------
    test_config : Mapping
        manually provided config mapping

    Returns
    -------
    app : Flask
        a flask Flask housing the application
    """
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "archerycalculator.sqlite"),
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

    app.register_blueprint(calculator.bp)
    # Not 100% sure next line is neccessary... TODO: investigate further
    app.add_url_rule("/", endpoint="calculator")

    app.register_blueprint(tables.bp)

    app.register_blueprint(rounds.bp)

    app.register_blueprint(info.bp)

    app.register_blueprint(about.bp)

    app.register_blueprint(extras.bp)

    db.init_app(app)

    return app


if __name__ == "__main__":
    execute_app = create_app()
    execute_app.run()
