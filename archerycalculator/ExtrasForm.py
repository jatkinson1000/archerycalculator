from wtforms import (
    Form,
    validators,
    IntegerField,
    SelectField,
    BooleanField,
)


class GroupForm(Form):
    known_group_size = IntegerField("", [validators.InputRequired("please provide.")])
    known_group_unit = SelectField("", [validators.InputRequired("please provide.")])
    known_dist = IntegerField("", [validators.InputRequired("please provide.")])
    known_dist_unit = SelectField("", [validators.InputRequired("please provide.")])


class RoundComparisonForm(Form):
    roundname = SelectField("Round", [validators.InputRequired("Please provide.")])
    score = IntegerField("Score", [validators.InputRequired("Please provide.")])
    compound = BooleanField(label="Compound bow", false_values=(False, ""))

    outdoor = BooleanField(label="Target outdoor", false_values=(False, ""))
    indoor = BooleanField(label="Target indoor", false_values=(False, ""))
    wafield = BooleanField(label="WA Field", false_values=(False, ""))
    ifaafield = BooleanField(label="IFAA Field", false_values=(False, ""))
    virounds = BooleanField(label="VI Rounds", false_values=(False, ""))
    unofficial = BooleanField(label="Unofficial Rounds", false_values=(False, ""))
