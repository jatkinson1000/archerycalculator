from wtforms import Form, validators, SearchField, IntegerField


class HCForm(Form):
    bowstyle = SearchField("Bowstyle", [validators.InputRequired("Please provide.")])
    gender = SearchField(
        "Gender under AGB", [validators.InputRequired("Please provide.")]
    )
    age = SearchField("Age category", [validators.InputRequired("Please provide.")])
    roundname = SearchField("Round", [validators.InputRequired("Please provide.")])
    score = IntegerField("Score", [validators.InputRequired("Please provide.")])
