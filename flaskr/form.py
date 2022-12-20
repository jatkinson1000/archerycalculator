from wtforms import Form, SearchField, validators


class HCForm(Form):
    bowstyle = SearchField(
        "Bowstyle", [validators.InputRequired("Please provide.")], list="bowstylelist"
    )
    roundname = SearchField("Round", [validators.InputRequired("Please provide.")])
    gender = SearchField("Gender under AGB")
    age = SearchField("Age category")
