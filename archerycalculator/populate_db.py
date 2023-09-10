"""Module of routined for populating the database with key data."""
from archeryutils import load_rounds
import archeryutils.classifications.classification_utils as class_func


bowstyles = class_func.read_bowstyles_json()

genders = class_func.read_genders_json()

ages = class_func.read_ages_json()

classes_in = class_func.read_classes_json("agb_indoor")

classes_out = class_func.read_classes_json("agb_outdoor")

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


def load_bowstyles_to_db(database):
    # AGB Target bowstyles from file
    for item in bowstyles:
        database.execute(
            "INSERT INTO bowstyles (bowstyle,disciplines) VALUES (?,?);",
            (item["bowstyle"], "TF"),
        )
    # Additional AGB field bowstyles
    for item in ["Traditional", "Flatbow"]:
        database.execute(
            "INSERT INTO bowstyles (bowstyle,disciplines) VALUES (?,?);",
            (item, "TF"),
        )
    database.commit()


def load_genders_to_db(database):
    for item in genders:
        database.execute("INSERT INTO genders (gender) VALUES (?);", [item])
    database.commit()


def load_ages_to_db(database):
    for item in ages:
        database.execute(
            "INSERT INTO ages (age_group,gov_body,male_dist,female_dist) VALUES (?,?,?,?);",
            (item["age_group"], "AGB", item["male"][0], item["female"][0]),
        )
    database.commit()


def load_rounds_to_db(database):
    for roundname, round_obj in rounds.items():
        database.execute(
            "INSERT INTO rounds (round_name,code_name,body,location,family) VALUES (?,?,?,?,?);",
            (
                round_obj.name,
                roundname,
                round_obj.body,
                round_obj.location,
                round_obj.family,
            ),
        )
    database.commit()


def load_classes_to_db(database):
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
