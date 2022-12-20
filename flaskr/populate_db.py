from archeryutils.archeryutils import (
    rounds,
    # handicap_equations as hc_eq,
    # handicap_functions as hc_func,
)


bowstyles = {
    "Compound": "TF",
    "Recurve": "TF",
    "Barebow": "TF",
    "longbow": "TF",
}

genders = ["Male", "Female"]

ages = {
    "Adult": "AGB",
    "Master (50+)": "AGB",
    "Under 21": "AGB",
    "Under 18": "AGB",
    "Under 16": "AGB",
    "Under 15": "AGB",
    "Under 14": "AGB",
    "Under 12": "AGB",
}

rounds = rounds.AGB_outdoor_imperial


def load_bowstyles(db):
    for item in bowstyles.items():
        db.execute(
            "INSERT INTO bowstyles (bowstyle,disciplines) VALUES (?,?);",
            (item[0], item[1]),
        )
    db.commit()


def load_genders(db):
    for item in genders:
        db.execute("INSERT INTO genders (gender) VALUES (?);", [item])
    db.commit()


def load_ages(db):
    for item in ages.items():
        db.execute(
            "INSERT INTO ages (age_group,gov_body) VALUES (?,?);", (item[0], item[1])
        )
    db.commit()


def load_rounds(db):
    for item in rounds:
        db.execute(
            "INSERT INTO rounds (round_name,code_name,gov_body) VALUES (?,?,?);",
            (rounds[item].name, item, "AGB"),
        )
    db.commit()
