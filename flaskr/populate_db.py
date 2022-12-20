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

genders = ["male", "female"]

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

rounds = list(rounds.AGB_outdoor_imperial.values())


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
            "INSERT INTO rounds (round_name,gov_body) VALUES (?,?);", (item.name, "AGB")
        )
    db.commit()
