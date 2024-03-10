"""Populate the database used by archerycalculator."""

import archeryutils.classifications.classification_utils as class_func
from archeryutils import load_rounds


def load_bowstyles_to_db(db):
    """Load AGB Target bowstyles from file plus any field ones."""
    bowstyles = class_func.read_bowstyles_json()
    for item in bowstyles:
        db.execute(
            "INSERT INTO bowstyles (bowstyle,disciplines) VALUES (?,?);",
            (item["bowstyle"], "TF"),
        )

    # Additional AGB field bowstyles
    for item in ["Traditional", "Flatbow"]:
        db.execute(
            "INSERT INTO bowstyles (bowstyle,disciplines) VALUES (?,?);",
            (item, "TF"),
        )
    db.commit()


def load_genders_to_db(db):
    """Load AGB genders from file."""
    genders = class_func.read_genders_json()
    for item in genders:
        db.execute("INSERT INTO genders (gender) VALUES (?);", [item])
    db.commit()


def load_ages_to_db(db):
    """Load AGB ages from file."""
    ages = class_func.read_ages_json()
    for item in ages:
        db.execute(
            (
                "INSERT INTO ages "
                "(age_group,gov_body,male_dist,female_dist) VALUES (?,?,?,?);"
            ),
            (item["age_group"], "AGB", item["male"][0], item["female"][0]),
        )
    db.commit()


def load_rounds_to_db(db):
    """Load rounds from file."""
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
            "Custom.json",
        ]
    )

    for item in rounds:
        db.execute(
            "INSERT INTO rounds (round_name,code_name,body,location,family) "
            "VALUES (?,?,?,?,?);",
            (
                rounds[item].name,
                item,
                rounds[item].body,
                rounds[item].location,
                (rounds[item].family if rounds[item].family else ""),
            ),
        )
    db.commit()


def load_classes_to_db(db):
    """Load AGB indoor and outdoor classes from file."""
    classes_in = class_func.read_classes_json("agb_indoor")
    classes_out = class_func.read_classes_json("agb_outdoor")

    for classes in [classes_in, classes_out]:
        for i, shortname in enumerate(classes["classes"]):
            db.execute(
                "INSERT INTO classes (shortname,longname,location) VALUES (?,?,?);",
                (shortname, classes["classes_long"][i], classes["location"]),
            )
        db.execute(
            "INSERT INTO classes (shortname,longname,location) VALUES (?,?,?);",
            ("UC", "Unclassified", classes["location"]),
        )
        db.commit()
