from archeryutils import rounds
from archeryutils.classifications import classifications as class_func


bowstyles = class_func.read_bowstyles_json()

genders = class_func.read_genders_json()

ages = class_func.read_ages_json()

classes = class_func.read_classes_json()

rounds = rounds.read_json_to_round_dict(
    [
        "AGB_outdoor_imperial.json",
        "AGB_outdoor_metric.json",
        # "AGB_indoor.json",
        "WA_outdoor.json",
        # "WA_indoor.json",
        # "Custom.json",
    ]
)


def load_bowstyles(db):
    for item in bowstyles:
        db.execute(
            "INSERT INTO bowstyles (bowstyle,disciplines) VALUES (?,?);",
            (item["bowstyle"], "TF"),
        )
    db.commit()


def load_genders(db):
    for item in genders:
        db.execute("INSERT INTO genders (gender) VALUES (?);", [item])
    db.commit()


def load_ages(db):
    for item in ages:
        db.execute(
            "INSERT INTO ages (age_group,gov_body) VALUES (?,?);",
            (item["age_group"], "AGB"),
        )
    db.commit()


def load_rounds(db):
    for item in rounds:
        db.execute(
            "INSERT INTO rounds (round_name,code_name,gov_body) VALUES (?,?,?);",
            (rounds[item].name, item, "AGB"),
        )
    db.commit()


def load_classes(db):
    for i, shortname in enumerate(classes["classes"]):
        db.execute(
            "INSERT INTO classes (shortname,longname) VALUES (?,?);",
            (shortname, classes["classes_long"][i]),
        )
    db.execute(
        "INSERT INTO classes (shortname,longname) VALUES (?,?);",
        ("UC", "Unclassified"),
    )
    db.commit()
