"""Generate and populate the database used by archerycalculator."""

import sqlite3

import click
from flask import current_app, g

from archerycalculator import populate_db


def get_db():
    """
    Make a database connection and store globals.

    Parameters
    ----------
    None

    Returns
    -------
    g.db : sqlite3.connect object
        database connection
    """
    # g is object for unique requests to the database
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        # Return rows as dicts when using cursor
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(err=None):
    """
    Close the database connection and remove from globals.

    Parameters
    ----------
    err : None
        required argument for function

    """
    database = g.pop("db", None)

    if database is not None:
        database.close()


def init_db():
    """Call the SQL functions in the schema.sql file to init the tables in db."""
    database = get_db()
    with current_app.open_resource("schema.sql") as db_file:
        database.executescript(db_file.read().decode("utf8"))
    populate_db.load_bowstyles_to_db(database)
    populate_db.load_ages_to_db(database)
    populate_db.load_genders_to_db(database)
    populate_db.load_rounds_to_db(database)
    populate_db.load_classes_to_db(database)


def query_db(query, args=(), one=False):
    """
    Execute a query to the database and return the result.

    Parameters
    ----------
    query : str
        SQL query to perform on the database
    args : Tuple[Any]
        arguments to pass to the
    one : bool
        return a single value?

    Returns
    -------
    ret_vals :

    """
    cur = get_db().execute(query, args)
    ret_vals = cur.fetchall()
    cur.close()
    return (ret_vals[0] if ret_vals else None) if one else ret_vals


def sql_to_lod(sql_result):
    """
    Convert the results of fetch one or fetch all to a list of dicts.

    Takes each item in the sql result and turns into a list of:
    {key : item[key]} for every key in item.

    E.g. query_db("SELECT age_group FROM ages") will return a list of sqlite objects
    of the form:
        [<age_group - 50+>, <age_group - adult>, <age_group - U21>, ...]
    This function will transform this into:
        [{"age_group" : "50+"}, {"age_group" : "adult"}, {"age_group" : "U21"}, ...]

    """
    try:
        unpacked = [{k: item[k] for k in item.keys()} for item in sql_result]
        return unpacked
    except Exception as err:
        # print(f"Failed to convert with error:{err}\n return empty list.")
        return []


def sql_to_dol(sql_result):
    """
    Convert the results of fetch one or fetch all to a single dict of lists.

    Takes each item in the sql result and turns into a list of:
    {key : item[key]} for every key in item.

    E.g. query_db("SELECT age_group FROM ages") will return a list of sqlite objects
    of the form:
        [<age_group - 50+>, <age_group - adult>, <age_group - U21>, ...]
    This function will transform this into:
        {"age_group" : ["50+", "adult", "U21", ...]}

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


def generate_enum_mapping(enum_class, query):
    """
    Generate a mapping dict from database query results to enum members.

    Used to provide a mapping from the string name displayed to users on the site to
    the enum member.

    Parameters
    ----------
    enum_class :
        the enum class to map to.
    query : str
        the sql query string to fetch enum_name and str_name pairs.

    Returns
    -------
    dict
        Dictionary mapping str_name to enum_class members.
    """
    results = query_db(query)
    return {str_name: enum_class[enum_name] for enum_name, str_name in results}


# define command line argument 'init-db' to run init_db function at startup
@click.command("init-db")
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


def init_app(app):
    """Close database when app is shut."""
    app.teardown_appcontext(close_db)

    # add init_db_command to be called from flask app
    app.cli.add_command(init_db_command)
