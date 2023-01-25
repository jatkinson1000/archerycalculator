from wtforms import (
    Form,
    validators,
    IntegerField,
    DecimalField,
    SelectField,
    BooleanField,
)


class HCForm(Form):
    bowstyle = SelectField("Bowstyle", [validators.InputRequired("Please provide.")])
    gender = SelectField(
        "Gender under AGB", [validators.InputRequired("Please provide.")]
    )
    age = SelectField("Age category", [validators.InputRequired("Please provide.")])
    roundname = SelectField("Round", [validators.InputRequired("Please provide.")])
    score = IntegerField("Score", [validators.InputRequired("Please provide.")])

    # Advanced options
    decimalHC = BooleanField(label="Return Decimal Handicap", false_values=(False, ""))
    diameter = DecimalField("Custom Arrow diameter [mm]", default=0.0, places=4)
    scheme = SelectField(
        "Handicap Scheme",
        choices=[
            ("AGB", "Archery GB"),
            ("AGBold", "Old Archery GB"),
            ("AA", "Archery Australia"),
            ("AA2", "Old Archery Australia"),
        ],
        coerce=str,
        validate_choice=False,
    )
