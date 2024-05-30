"""Populate the database used by archerycalculator."""

import archeryutils.classifications.classification_utils as class_func
from archeryutils import load_rounds


def load_bowstyles_to_db(database):
    """
    Load bowstyles into database.

    Parameters
    ----------
    database :
        sqlite database connection

    Returns
    -------
    None
    """
    bowstyles = class_func.read_bowstyles_json()
    for item in bowstyles:
        database.execute(
            "INSERT INTO bowstyles (bowstyle,disciplines) VALUES (?,?);",
            (item["bowstyle"], "TF"),
        )


def load_genders_to_db(database):
    """
    Load AGB genders from file into database.

    Parameters
    ----------
    database :
        sqlite database connection
    """
    genders = class_func.read_genders_json()
    for item in genders:
        database.execute("INSERT INTO genders (gender) VALUES (?);", [item])
    database.commit()


def load_ages_to_db(database):
    """
    Load AGB ages from file into database.

    Parameters
    ----------
    database :
        sqlite database connection
    """
    ages = class_func.read_ages_json()
    for item in ages:
        database.execute(
            "INSERT INTO ages (age_group,gov_body,male_dist,female_dist,red_dist_max,red_dist_min,blue_dist_max,blue_dist_min) VALUES (?,?,?,?,?,?,?,?);",
            (
                item["age_group"],
                "AGB",
                item["male"][0],
                item["female"][0],
                item["red"][1],
                item["red"][0],
                item["blue"][1],
                item["blue"][0],
            ),
        )
    database.commit()


def load_rounds_to_db(database):
    """
    Load rounds from file into database.

    Parameters
    ----------
    database :
        sqlite database connection
    """
    rounds = load_rounds.read_json_to_round_dict(
        [
            "AGB_outdoor_imperial.json",
            "AGB_outdoor_metric.json",
            "AGB_indoor.json",
            "WA_outdoor.json",
            "WA_indoor.json",
            "AGB_VI.json",
            "WA_VI.json",
            "WA_field.json",
            "IFAA_field.json",
            "Miscellaneous.json",
        ]
    )

    for roundname, round_obj in rounds.items():
        database.execute(
            "INSERT INTO rounds (round_name,code_name,body,location,family) "
            "VALUES (?,?,?,?,?);",
            (
                round_obj.name,
                roundname,
                round_obj.body,
                round_obj.location,
                (round_obj.family if round_obj.family else ""),
            ),
        )
    database.commit()


def load_classes_to_db(database):
    """
    Load AGB indoor and outdoor classes from file into database.

    Parameters
    ----------
    database :
        sqlite database connection
    """
    classes_in = class_func.read_classes_json("agb_indoor")
    classes_out = class_func.read_classes_json("agb_outdoor")

    for classes in [classes_in, classes_out]:
        for i, shortname in enumerate(classes["classes"]):
            database.execute(
                "INSERT INTO classes (shortname,longname,location) VALUES (?,?,?);",
                (shortname, classes["classes_long"][i], classes["location"]),
            )
        database.execute(
            "INSERT INTO classes (shortname,longname,location) VALUES (?,?,?);",
            ("UC", "Unclassified", classes["location"]),
        )
        database.commit()
