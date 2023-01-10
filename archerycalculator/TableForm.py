from wtforms import Form, validators, SearchField, SelectField, BooleanField


class HandicapTableForm(Form):
    round1 = SearchField("Round1", [validators.InputRequired("Please provide.")])
    round2 = SearchField("Round2")
    round3 = SearchField("Round3")
    round4 = SearchField("Round4")
    round5 = SearchField("Round5")
    round6 = SearchField("Round6")
    round7 = SearchField("Round7")
    allowance = BooleanField(label="Create Allowance Table", false_values=(False, ""))


class ClassificationTableForm(Form):
    bowstyle = SelectField("Bowstyle", [validators.InputRequired("Please provide.")])
    gender = SelectField(
        "Gender under AGB", [validators.InputRequired("Please provide.")]
    )
    age = SelectField("Age category", [validators.InputRequired("Please provide.")])
