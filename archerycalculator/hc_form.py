"""Form for main calculator coded using wtforms."""

from wtforms import (
    BooleanField,
    DecimalField,
    Form,
    IntegerField,
    SelectField,
    validators,
)


class HCForm(Form):
    """Class for main calculator form."""

    bowstyle = SelectField(
        label="Bowstyle", validators=[validators.InputRequired("Please provide.")]
    )
    gender = SelectField(
        label="Gender under AGB",
        validators=[validators.InputRequired("Please provide.")],
    )
    age = SelectField(
        label="Age category", validators=[validators.InputRequired("Please provide.")]
    )
    roundname = SelectField(
        label="Round", validators=[validators.InputRequired("Please provide.")]
    )
    score = IntegerField(
        label="Score", validators=[validators.InputRequired("Please provide.")]
    )

    # Advanced options
    decimalHC = BooleanField(label="Return Decimal Handicap", false_values=(False, ""))
    diameter = DecimalField(label="Custom Arrow diameter [mm]", default=0.0, places=4)
    scheme = SelectField(
        label="Handicap Scheme",
        choices=[
            ("AGB", "Archery GB"),
            ("AGBold", "Old Archery GB"),
            ("AA", "Archery Australia"),
            ("AA2", "Old Archery Australia"),
        ],
        coerce=str,
        validate_choice=False,
    )
