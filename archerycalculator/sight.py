"""Code for sight functionalities on archerycalculator."""

import numpy as np
from flask import (
    Blueprint,
    render_template,
    request,
)

from archerycalculator import sight_form

bp = Blueprint("sight", __name__, url_prefix="/sight")


@bp.route("/distance-conversion", methods=("GET", "POST"))
def distance_conversion():
    """
    Convert yards to metres and vice versa.

    Returns
    -------
    html template :
        call to html templating function
    """
    # Load form and set defaults
    form = sight_form.DistanceForm(
        request.form,
    )

    # Set form choices
    form.units_direction.choices = ["yards to metres", "metres to yards"]

    if request.method == "POST" and form.validate():
        # Get essential form results
        units_direction = request.form["units_direction"]
        min_dist = float(request.form["min_dist"])
        max_dist = float(request.form["max_dist"])
        increment_dist = float(request.form["increment_dist"])
        form.increment_dist.default = 10.0

        # Check the inputs are all valid
        min_dist = abs(min_dist)
        max_dist = abs(max_dist)
        increment_dist = abs(increment_dist)
        if min_dist > max_dist:
            min_dist, max_dist = max_dist, min_dist

        if units_direction == "metres to yards":
            scale_factor = 1.0 / 0.9144
            unit_from = "metres"
            unit_to = "yards"
        else:
            scale_factor = 0.9144
            unit_from = "yards"
            unit_to = "metres"

        dist_array_in = np.arange(min_dist, max_dist+increment_dist, increment_dist)
        dist_array_out = dist_array_in * scale_factor

        results  = zip(dist_array_in, dist_array_out)  # array with units names at top, and then pairs of values going down

        # Return the results
        return render_template(
            "distances.html",
            form=form,
            results=results,
            unit_from=unit_from,
            unit_to=unit_to,
        )

    # If first visit load the default form with no inputs
    return render_template(
        "distances.html",
        form=form,
        results=None,
    )
