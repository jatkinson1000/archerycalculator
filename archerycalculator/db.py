"""Definitions for database."""
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


def close_db(err=None):
    database = g.pop("db", None)

    if database is not None:
        database.close()


def init_db():
    # call the SQL functions in the schema.sql file to init the tables in db
    database = get_db()
    with current_app.open_resource("schema.sql") as db_file:
        database.executescript(db_file.read().decode("utf8"))
    populate_db.load_bowstyles_to_db(database)
    populate_db.load_ages_to_db(database)
    populate_db.load_genders_to_db(database)
    populate_db.load_rounds_to_db(database)
    populate_db.load_classes_to_db(database)


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    ret_vals = cur.fetchall()
    cur.close()
    return (ret_vals[0] if ret_vals else None) if one else ret_vals


def sql_to_lod(sql_result):
    """
    Converts the results of fetch one or fetch all to a list of dicts
    """
    try:
        unpacked = [{k: item[k] for k in item.keys()} for item in sql_result]
        return unpacked
    except Exception as err:
        # print(f"Failed to convert with error:{err}\n return empty list.")
        return []


def sql_to_dol(sql_result):
    """
    Converts the results of fetch one or fetch all to a single dict of lists
    """
    try:
        # unpacked = {k: [d[k] for d in sql_result] for k in sql_result[0].keys()}
        unpacked = {
            k: [d[k] for d in sql_result if k in d.keys()] for k in sql_result[0].keys()
        }
        return unpacked
    except Exception as err:
        # print(f"Failed to convert with error:{err}\n return empty dict.")
        return {}


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
