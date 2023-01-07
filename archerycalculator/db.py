import sqlite3

import click
from flask import current_app, g

from archerycalculator import populate_db


def get_db():
    # g is object for unique requests to the database
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        # Return rows as dicts when using cursor
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    # call the SQL functions in the schema.sql file to init the tables in db
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))
    populate_db.load_bowstyles(db)
    populate_db.load_ages(db)
    populate_db.load_genders(db)
    populate_db.load_rounds(db)
    populate_db.load_classes(db)


# define command line argument 'init-db' to run init_db function at startup
@click.command("init-db")
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


def init_app(app):
    # close database when app is shut
    app.teardown_appcontext(close_db)
    # add init_db_command to be called from flask app
    app.cli.add_command(init_db_command)
