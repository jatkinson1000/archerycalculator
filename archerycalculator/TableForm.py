from wtforms import Form, validators, SelectField, BooleanField


class HandicapTableForm(Form):
    round1 = SelectField("Round1", [validators.InputRequired("Please provide.")])
    round1_compound = BooleanField(
        label="Use compound scoring", false_values=(False, "")
    )
    round2 = SelectField("Round2")
    round2_compound = BooleanField(
        label="Use compound scoring", false_values=(False, "")
    )
    round3 = SelectField("Round3")
    round3_compound = BooleanField(
        label="Use compound scoring", false_values=(False, "")
    )
    round4 = SelectField("Round4")
    round4_compound = BooleanField(
        label="Use compound scoring", false_values=(False, "")
    )
    round5 = SelectField("Round5")
    round5_compound = BooleanField(
        label="Use compound scoring", false_values=(False, "")
    )
    round6 = SelectField("Round6")
    round6_compound = BooleanField(
        label="Use compound scoring", false_values=(False, "")
    )
    round7 = SelectField("Round7")
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
    discipline = SelectField("Discipline")
