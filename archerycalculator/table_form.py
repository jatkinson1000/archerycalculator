"""Forms for tables functionalities coded using wtforms."""

from wtforms import BooleanField, Form, SelectField, validators


class HandicapTableForm(Form):
    """
    Class for handicap table form.

    Attributes
    ----------
    roundn : SelectField
        round n/7 to display handicaqp table for.
    roundn_compound : BooleanField
        use compound scoring for round n?
    allowance : BooleanField
        generate allowance tables instead of handicap tables?

    """

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
    """
    Class for classification table form.

    Attributes
    ----------
    bowstyle : SelectField
        bowstyle to use
    gender : SelectField
        gender to use
    age : SelectField
        age to use
    discipline : SelectField
        discipline to use

    """

    bowstyle = SelectField("Bowstyle", [validators.InputRequired("Please provide.")])
    gender = SelectField(
        "Gender under AGB", [validators.InputRequired("Please provide.")]
    )
    age = SelectField("Age category", [validators.InputRequired("Please provide.")])
    discipline = SelectField("Discipline")


class EventTableForm(Form):
    """
    Class for classification by event table form.

    Attributes
    ----------
    bowstyle : SelectField
        bowstyle to use
    roundfamily : SelectField
        roundfamily to generate table for
    restrict_to_named : BooleanField
        restrict to named round or use full range of distances?

    """

    bowstyle = SelectField("Bowstyle", [validators.InputRequired("Please provide.")])
    roundfamily = SelectField("RoundFamily")
    restrict_to_named = BooleanField(
        label="Restrict to named round", false_values=(False, "")
    )
