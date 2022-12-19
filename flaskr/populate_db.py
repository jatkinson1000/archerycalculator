from flask import g


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


def load_bowstyles(db):
    cur = db.cursor()
    for item in bowstyles.items():
        db.execute(
            "INSERT INTO bowstyles (bowstyle,disciplines) VALUES (?,?);",
            (item[0], item[1]),
        )
    db.commit()

def load_genders(db):
    cur = db.cursor()
    for item in genders:
        db.execute("INSERT INTO genders (gender) VALUES (?);", [item])
    db.commit()


def load_ages(db):
    cur = db.cursor()
    for item in ages.items():
        db.execute(
            "INSERT INTO ages (age_group,gov_body) VALUES (?,?);", (item[0], item[1])
        )
    db.commit()
