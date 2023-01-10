from wtforms import Form, validators, SearchField, SelectField, BooleanField


class HandicapTableForm(Form):
    round1 = SearchField("Round1", [validators.InputRequired("Please provide.")])
    round1_compound = BooleanField(
        label="Use compound scoring", false_values=(False, "")
    )
    round2 = SearchField("Round2")
    round2_compound = BooleanField(
        label="Use compound scoring", false_values=(False, "")
    )
    round3 = SearchField("Round3")
    round3_compound = BooleanField(
        label="Use compound scoring", false_values=(False, "")
    )
    round4 = SearchField("Round4")
    round4_compound = BooleanField(
        label="Use compound scoring", false_values=(False, "")
    )
    round5 = SearchField("Round5")
    round5_compound = BooleanField(
        label="Use compound scoring", false_values=(False, "")
    )
    round6 = SearchField("Round6")
    round6_compound = BooleanField(
        label="Use compound scoring", false_values=(False, "")
    )
    round7 = SearchField("Round7")
    round7_compound = BooleanField(
        label="Use compound scoring", false_values=(False, "")
    )
    allowance = BooleanField(label="Create Allowance Table", false_values=(False, ""))


class ClassificationTableForm(Form):
    bowstyle = SelectField("Bowstyle", [validators.InputRequired("Please provide.")])
    gender = SelectField(
        "Gender under AGB", [validators.InputRequired("Please provide.")]
    )
    age = SelectField("Age category", [validators.InputRequired("Please provide.")])
    discipline = SelectField(
        "Discipline",
        choices=[("outdoor", "Target Outdoor"), ("indoor", "Target Indoor")],
    )
