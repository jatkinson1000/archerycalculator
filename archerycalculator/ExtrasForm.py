from wtforms import (
    Form,
    validators,
    IntegerField,
    SelectField,
)


class GroupForm(Form):
    known_group_size = IntegerField("", [validators.InputRequired("Please provide.")])
    known_group_unit = SelectField("", [validators.InputRequired("Please provide.")])
    known_dist = IntegerField("", [validators.InputRequired("Please provide.")])
    known_dist_unit = SelectField("", [validators.InputRequired("Please provide.")])
