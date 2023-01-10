from wtforms import Form, validators, SearchField, IntegerField, DecimalField, SelectField, BooleanField


class HCForm(Form):
    bowstyle = SearchField("Bowstyle", [validators.InputRequired("Please provide.")])
    gender = SearchField(
        "Gender under AGB", [validators.InputRequired("Please provide.")]
    )
    age = SearchField("Age category", [validators.InputRequired("Please provide.")])
    roundname = SearchField("Round", [validators.InputRequired("Please provide.")])
    score = IntegerField("Score", [validators.InputRequired("Please provide.")])
 
    # Advanced options
    decimalHC = BooleanField(label="Return Decimal Handicap", false_values=(False, ""))
    diameter = DecimalField("Custom Arrow diameter [mm]", default=0.0, places=4)
    scheme = SelectField("Handicap Scheme", choices=[('AGB', 'Archery GB'), ('AGBold', 'Old Archery GB'), ('AA', 'Archery Australia'), ('AA2', 'Old Archery Australia')], coerce=str, validate_choice=False)
