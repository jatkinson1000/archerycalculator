"""Populate the database used by archerycalculator."""

import archeryutils.classifications.classification_utils as cf
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
    bowstyles = cf.read_bowstyles_json()
    for bowstyle_id, bowstyle_data in bowstyles.items():
        # Hardcode "Longbow" from archeryutils to "English Longbow" for display
        if bowstyle_data["bowstyle"] == "Longbow":
            bowstyle_data["bowstyle"] = "English Longbow"

        database.execute(
            "INSERT INTO bowstyles (bowstyle_enum,bowstyle,disciplines) VALUES (?,?,?);",
            (bowstyle_id, bowstyle_data["bowstyle"], "TF"),
        )


def load_genders_to_db(database):
    """
    Load AGB genders from file into database.

    Parameters
    ----------
    database :
        sqlite database connection
    """
    genders = cf.read_genders_json()
    for item in genders:
        database.execute("INSERT INTO genders (gender_enum,gender) VALUES (?,?);", (item.upper(), item))
    database.commit()


def load_ages_to_db(database):
    """
    Load AGB ages from file into database.

    Parameters
    ----------
    database :
        sqlite database connection
    """
    ages = cf.read_ages_json()
    for age_id, age_data in ages.items():
        database.execute(
            "INSERT INTO ages (age_enum,age_group,gov_body,male_dist,female_dist,sighted_dist_max,sighted_dist_min,unsighted_dist_max,unsighted_dist_min) VALUES (?,?,?,?,?,?,?,?,?);",
            (
                age_id,
                age_data["age_group"],
                "AGB",
                age_data["male"][0],
                age_data["female"][0],
                age_data["sighted"][1],
                age_data["sighted"][0],
                age_data["unsighted"][1],
                age_data["unsighted"][0],
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
            "WA_experimental.json",
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
    classes_in = cf.read_classes_json("agb_indoor")
    classes_out = cf.read_classes_json("agb_outdoor")

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
