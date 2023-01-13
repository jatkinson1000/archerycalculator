from flask import (
    Blueprint,
    render_template,
    request,
)
import numpy as np

from archerycalculator.db import query_db, sql_to_dol

from archeryutils import rounds
from archeryutils.handicaps import handicap_equations as hc_eq
from archeryutils.handicaps import handicap_functions as hc_func

from archerycalculator import ExtrasForm, utils

bp = Blueprint("extras", __name__, url_prefix="/extras")


# Single home page (for now)
@bp.route("/groups", methods=("GET", "POST"))
def groups():

    # Load form and set defaults
    form = ExtrasForm.GroupForm(
        request.form,
    )

    # Set form choices
    form.known_group_unit.choices = ["cm", "inches"]
    form.known_dist_unit.choices = ["metres", "yards"]

    error = None
    if request.method == "POST" and form.validate():

        # Get essential form results
        known_group_size = float(request.form["known_group_size"])
        known_group_unit = request.form["known_group_unit"]
        known_dist = float(request.form["known_dist"])
        known_dist_unit = request.form["known_dist_unit"]

        # Check the inputs are all valid
        known_group_size = abs(known_group_size)
        known_dist = abs(known_dist)
        
        if known_group_unit == "cm":
            group_scale_factor = 1e-2
            group_unit = "cm"
        else:
            group_scale_factor = 2.54e-2
            group_unit = "in"
        
        if known_dist_unit == "metres":
            dists = np.asarray([18., 20., 30., 40., 50., 60., 70., 90.])
            dist_scale_factor = 1.0
            dist_unit = "m"
        else:
            dists = np.asarray([20., 30., 40., 50., 60., 80., 100.])
            dist_scale_factor = 0.9144
            dist_unit = "yd"
        
        # Generate the handicap params
        hc_params = hc_eq.HcParams()
        hc_scheme = "AGB"

        # Calculate the handicap
        known_sig_r = known_group_size * group_scale_factor / 2.0

        def f_root(h, scheme, distance, hc_params):
            val = hc_eq.sigma_r(h, scheme, distance, hc_params)
            return val - known_sig_r

        # Rootfind value of sigma_r
        handicap = utils.rootfinding(-75, 300, f_root, hc_scheme, known_dist*dist_scale_factor, hc_params)

        # Map to other distances
        sig_r = hc_eq.sigma_r(handicap, hc_scheme, dists*dist_scale_factor, hc_params)

        # Calculate group sizes
        groups = 2.0 * sig_r

        icons = [None] * len(groups)
        for i, group in enumerate(groups):
            icons[i] = utils.group_icons(group)
       
        results = dict(zip(dists, zip(groups/group_scale_factor, icons)))
        print(results)

        # Return the results
        return render_template(
            "extras.html",
            form=form,
            results=results,
            group_unit=group_unit,
            dist_unit=dist_unit,
            )

    # If first visit load the default form with no inputs
    return render_template(
        "extras.html",
        form=form,
        results=None,
    )
