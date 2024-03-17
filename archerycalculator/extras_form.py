"""Forms for 'extra' functionalities coded using wtforms."""

from wtforms import (
    BooleanField,
    Form,
    IntegerField,
    SelectField,
    validators,
)


class GroupForm(Form):
    """
    Class for classification by event table form.

    Attributes
    ----------
    known_group_size : IntegerField
        input group size
    known_group_unit : SelectField
        input group size unit of measurement
    known_dist : IntegerField
        input distance
    known_dist_unit : SelectField
        input distance unit of measurement
    """

    known_group_size = IntegerField("", [validators.InputRequired("please provide.")])
    known_group_unit = SelectField("", [validators.InputRequired("please provide.")])
    known_dist = IntegerField("", [validators.InputRequired("please provide.")])
    known_dist_unit = SelectField("", [validators.InputRequired("please provide.")])


class RoundComparisonForm(Form):
    """
    Class for classification by event table form.

    Attributes
    ----------
    roundname : SelectField
        round to compare to
    score : IntegerField
        score to compare to
    compound : BooleanField
        perform analysis for compound bow?
    outdoor : BooleanField
        use outdoor rounds?
    indoor : BooleanField
        use indoor rounds?
    wafield : BooleanField
        use wa field rounds?
    ifaafield : BooleanField
        use ifaa field rounds?
    virounds : BooleanField
        use vi rounds?
    unofficial : BooleanField
        use unofficial rounds?
    """

    roundname = SelectField("Round", [validators.InputRequired("Please provide.")])
    score = IntegerField("Score", [validators.InputRequired("Please provide.")])
    compound = BooleanField(label="Compound bow", false_values=(False, ""))

    outdoor = BooleanField(label="Target outdoor", false_values=(False, ""))
    indoor = BooleanField(label="Target indoor", false_values=(False, ""))
    wafield = BooleanField(label="WA Field", false_values=(False, ""))
    ifaafield = BooleanField(label="IFAA Field", false_values=(False, ""))
    virounds = BooleanField(label="VI Rounds", false_values=(False, ""))
    unofficial = BooleanField(label="Unofficial Rounds", false_values=(False, ""))
