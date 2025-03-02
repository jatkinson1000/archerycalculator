"""Forms for sight functionalities coded using wtforms."""

from wtforms import (
    Form,
    FloatField,
    SelectField,
    validators,
)


class DistanceForm(Form):
    """
    Class for distance conversion form.

    Attributes
    ----------
    units_direction : SelectField
        metres to yards or yards to metres
    min_dist : FloatField
        minimum distance to use
    max_dist : FloatField
        maximum distance to use
    increment_dist : FloatField
        increment distance to use from min to max
    """

    units_direction = SelectField("Units conversion", [validators.InputRequired("please provide.")])
    min_dist =  FloatField("Minimum distance", [validators.InputRequired("please provide."), validators.NumberRange(min=0.0, max=1000.0)])
    max_dist =  FloatField("Maximum distance", [validators.InputRequired("please provide."), validators.NumberRange(min=0.0, max=1000.0)])
    increment_dist = FloatField("Increment", [validators.InputRequired("please provide."), validators.NumberRange(min=0.1, max=100.0)], default=10.0)

