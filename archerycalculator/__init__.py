"""Web app for archerycalculator."""

import contextlib
import os

from flask import Flask
from flask_sitemap import Sitemap

from archerycalculator import (
    about,
    calculator,
    db,
    extras,
    info,
    rounds,
    tables,
    new_field,
    sight,
)


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
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "archerycalculator.sqlite"),
    )

    ext = Sitemap(app=app)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    with contextlib.suppress(OSError):
        os.makedirs(app.instance_path)

    from archerycalculator import calculator

    app.register_blueprint(calculator.bp)
    # Not 100% sure next line is neccessary... TODO: investigate further
    app.add_url_rule("/", endpoint="calculator.calculator")

    @ext.register_generator
    def calculator():
        """Register / (calculator page) on sitemap."""
        yield "calculator.calculator", {}

    app.register_blueprint(tables.bp)

    @ext.register_generator
    def handicap_tables():
        """Register /tables/handicap on sitemap."""
        yield "tables.handicap_tables", {}

    @ext.register_generator
    def classification_tables():
        """Register /tables/classification on sitemap."""
        yield "tables.classification_tables", {}

    @ext.register_generator
    def print_classification_tables():
        """Register /tables/classification on sitemap."""
        yield "tables.print_classification_tables", {}

    @ext.register_generator
    def event_tables():
        """Register /tables/classbyevent on sitemap."""
        yield "tables.event_tables", {}

    app.register_blueprint(rounds.bp)

    @ext.register_generator
    def round_page():
        """Register /rounds on sitemap."""
        yield "rounds.rounds_page", {}

    app.register_blueprint(info.bp)

    @ext.register_generator
    def info_page():
        """Register /info on sitemap."""
        yield "info.info", {}

    app.register_blueprint(about.bp)

    @ext.register_generator
    def about_page():
        """Register /about on sitemap."""
        yield "about.about", {}

    app.register_blueprint(extras.bp)

    @ext.register_generator
    def groups():
        """Register /extras/groups on sitemap."""
        yield "extras.groups", {}

    @ext.register_generator
    def roundcomparison():
        """Register /extras/roundscomparison on sitemap."""
        yield "extras.roundcomparison", {}

    app.register_blueprint(new_field.bp)

    @ext.register_generator
    def rounds_page():
        """Register /new-field on sitemap."""
        yield "new-field.rounds_page", {}

    app.register_blueprint(sight.bp)

    @ext.register_generator
    def distance_conversion():
        """Register /sight/distance-conversion on sitemap."""
        yield "sight.distance_conversion", {}

    db.init_app(app)

    return app


if __name__ == "__main__":
    execute_app = create_app()
    execute_app.run()
