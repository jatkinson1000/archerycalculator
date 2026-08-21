"""Module of useful utilities for archerycalculator."""

import re

import numpy as np

from archerycalculator.db import query_db, sql_to_dol


def check_blacklist(roundlist, age, gender, bowstyle):
    """
    Filter rounds to remove any we don't want showing up on tables.

    Parameters
    ----------
    roundlist : list
        list of archeryutils round codenames
    age : str
        string descriptor of age category
    gender : str
        string descriptor of gender category
    bowstyle : str
        string descriptor of bowstyle category

    Returns
    -------
    saferounds : list
        filtered version of the input list

    """
    blacklist = []

    blacklist.append("wa_1440_90_6_zone")
    blacklist.append("wa_1440_70_6_zone")
    blacklist.append("wa_1440_60_6_zone")

    # Triple face rounds indoor
    blacklist.append("bray_i_triple")
    blacklist.append("bray_ii_triple")
    blacklist.append("portsmouth_triple")
    blacklist.append("wa_18_triple")
    blacklist.append("wa_25_triple")
    blacklist.append("worcester_5_spot")
    blacklist.append("vegas_300_triple")

    saferounds = []
    for roundname in roundlist:
        if roundname not in blacklist:
            saferounds.append(roundname)

    return saferounds


def indoor_display_filter(rounddict):
    """
    Filter indoor rounds to remove compound subscript for the purposes of display.

    Parameters
    ----------
    rounddict : dict
        dict of round data where the archeryutils codename is the key

    Returns
    -------
    list
        list of full round names from filtered version of the input dict

    """
    for roundname in list(rounddict.keys()):
        if "compound" in roundname:
            del rounddict[roundname]
    return [rounddict[round_i] for round_i in rounddict]


def get_compound_codename(round_codenames):
    """
    Convert any indoor rounds with special compound scoring to the compound format.

    Parameters
    ----------
    round_codenames : str or list of str
        list of str round codenames to check

    Returns
    -------
    round_codenames : str or list of str
        list of amended round codenames for compound

    """
    notlistflag = False
    if not isinstance(round_codenames, list):
        round_codenames = [round_codenames]
        notlistflag = True

    convert_dict = {
        "bray_i": "bray_i_compound",
        "bray_i_triple": "bray_i_compound_triple",
        "bray_ii": "bray_ii_compound",
        "bray_ii_triple": "bray_ii_compound_triple",
        "stafford": "stafford_compound",
        "portsmouth": "portsmouth_compound",
        "portsmouth_triple": "portsmouth_compound_triple",
        "vegas": "vegas_compound",
        "wa_18": "wa_18_compound",
        "wa_18_triple": "wa_18_compound_triple",
        "wa_25": "wa_25_compound",
        "wa_25_triple": "wa_25_compound_triple",
    }

    for i, codename in enumerate(round_codenames):
        if codename in convert_dict:
            round_codenames[i] = convert_dict[codename]
    if notlistflag:
        return round_codenames[0]
    return round_codenames


def check_alias(round_codename, age, gender, bowstyle):
    """
    select the 'appropriate' round from aliases.

    Parameters
    ----------
    round_codename : str
        str round codename to check
    age : str
        string descriptor of age category
    gender : str
        string descriptor of gender category
    bowstyle : str
        string descriptor of bowstyle category

    Returns
    -------
    round_codename : str
        amended round codenames

    """
    # WA900s
    if round_codename == "agb_900_60":
        round_codename = "wa_900"

    return round_codename


def order_rounds(rounds):
    """
    Given an iterator of rounds, sort them into an approved order.

    Parameters
    ----------
    rounds : dict of str:str
        dictionary of round codenames mapped to their family

    Returns
    -------
    sorted_rounds : dict of str:str
        dict of sorted rounds input dict

    """
    # Sort by family - rounds should already sorted within families. and filtered.
    order = [
        # OUTDOOR
        "york_hereford_bristol",
        "st_george_albion_windsor",
        "national",
        "western",
        "warwick",
        "american",
        "st_nicholas",
        "wa_1440",
        "wa_900",
        # 720 have special treatment
        "wa_720",
        "agb_long_metric",
        "agb_short_metric",
        # INDOOR
        # FIELD
        "wafield_24_marked",
        "wafield_24_unmarked",
        "wafield_24_mixed",
        "wafield_12_marked",
        "wafield_12_unmarked",
        "wafield_12_mixed",
        "ifaafield",
    ]

    sorted_rounds = {}
    for family in order:
        if family == "wa_720":
            # # Special treatment needed to sort the wa720 and metric720 families

            # Get all wa_720 rounds
            rounds_720 = {
                key: value
                for (key, value) in rounds.items()
                if value == "wa_720"
            }

            def _extract_720_info(codename: str) -> int:
                """Extract distance and face size from round codename with regex."""
                match = re.search(r"_(\d{2})_(\d{2,3})$", codename)
                if match:
                    return int(match.group(1)), int(match.group(2))
                # Fallback
                return 0, 0

            # Sort by: 1) 122 vs 80 face, 2) distance (descending), 3) name
            sorted_720_rounds = sorted(
                rounds_720.items(),
                key=lambda item: (
                    # Group: 0 for 122cm faces, 1 for 80cm
                    0 if _extract_720_info(item[0])[1] == 122 else 1,
                    # Distance (descending so take -ve)
                    -_extract_720_info(item[0])[0],
                    # Name for consistency
                    item[0]
                )
            )

            sorted_rounds.update(dict(sorted_720_rounds))

        elif family == "wa_1440":
            # # Special treatment needed to sort the wa720 and metric720 families

            # Get all rounds
            rounds_1440 = {
                key: value
                for (key, value) in rounds.items()
                if value == family
            }

            def _extract_1440_info(codename: str) -> int:
                """Extract distance from round codename with regex."""
                match = re.search(r"_(\d{2})$", codename)
                if match:
                    return int(match.group(1))
                # Fallback
                return 0

            # Sort by: 1) distance (descending), 2) name
            sorted_1440_rounds = sorted(
                rounds_1440.items(),
                key=lambda item: (
                    # Distance (descending so take -ve)
                    -_extract_1440_info(item[0]),
                    # Name for consistency
                    item[0]
                )
            )

            sorted_rounds.update(dict(sorted_1440_rounds))

        elif family == "wa_900":
            wa_900_rounds = {k: v for k, v in rounds.items() if v == "wa_900"}

            def _900_distance(codename):
                if codename == "wa_900":
                    return 60
                match = re.search(r"_(\d{2})$", codename)
                if match:
                    return int(match.group(1))
                # Fallback
                return 0

            for codename in sorted(wa_900_rounds, key=lambda c: -_900_distance(c)):
                sorted_rounds[codename] = wa_900_rounds[codename]

        elif family == "ifaafield":
            # Select full rounds first, then units
            sorted_rounds.update(
                {key: value for (key, value) in rounds.items() if "unit" not in key}
            )
        else:
            sorted_rounds.update(
                {key: value for (key, value) in rounds.items() if value == family}
            )

    # Catch any rounds in the list that are not included in the families listed above
    sorted_rounds.update({codename: rounds[codename] for codename in rounds})

    return sorted_rounds


def fetch_and_sort_rounds(location, body):
    """
    Fetch rounds for a given location and body from database and order.

    Parameters
    ----------
    location : Union str, list
        location to match
    body : Union str, list
        governing body to match

    Returns
    -------
    sorted : dict of str: str
    """
    if not isinstance(location, list):
        location = [location]
    if not isinstance(body, list):
        body = [body]

    db_rounds = sql_to_dol(
        query_db(
            "SELECT code_name,round_name,family FROM rounds "
            f"""WHERE location IN ('{"', '".join(location)}') """
            f"""AND body in ('{"', '".join(body)}')"""
        )
    )

    rounds_names = dict(zip(db_rounds["code_name"], db_rounds["round_name"]))
    rounds_families = dict(zip(db_rounds["code_name"], db_rounds["family"]))
    ordered_names = list(order_rounds(rounds_families).keys())

    return_rounds = {
        "code_name": ordered_names,
        "round_name": [rounds_names[codename] for codename in ordered_names],
    }

    return return_rounds


def rootfinding(x_min, x_max, f_root, *args):
    """
    For bracket and function find the value such that f=0.

    Parameters
    ----------
    x_min : float
        lower bound of the search bracket
    x_max : float
        upper bound of the search bracket
    f_root : function
        function to minimise
    args :
        arguments to f_root

    Returns
    -------
    hc : float
        root of function

    References
    ----------
    Brent's Method for Root Finding in Scipy
    - https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.brentq.html
    - https://github.com/scipy/scipy/blob/dde39b7cc7dc231cec6bf5d882c8a8b5f40e73ad/
      scipy/optimize/Zeros/brentq.c

    """
    x = [x_min, x_max]
    f = [
        f_root(x[0], *args),
        f_root(x[1], *args),
    ]
    xtol = 1.0e-16
    rtol = 0.00
    xblk = 0.0
    fblk = 0.0
    scur = 0.0
    spre = 0.0
    dpre = 0.0
    dblk = 0.0
    stry = 0.0

    if abs(f[1]) <= f[0]:
        xcur = x[1]
        xpre = x[0]
        fcur = f[1]
        fpre = f[0]
    else:
        xpre = x[1]
        xcur = x[0]
        fpre = f[1]
        fcur = f[0]

    for _ in range(50):
        if (fpre != 0.0) and (fcur != 0.0) and (np.sign(fpre) != np.sign(fcur)):
            xblk = xpre
            fblk = fpre
            spre = xcur - xpre
            scur = xcur - xpre
        if abs(fblk) < abs(fcur):
            xpre = xcur
            xcur = xblk
            xblk = xpre

            fpre = fcur
            fcur = fblk
            fblk = fpre

        delta = (xtol + rtol * abs(xcur)) / 2.0
        sbis = (xblk - xcur) / 2.0

        if (fcur == 0.0) or (abs(sbis) < delta):
            hc = xcur
            break

        if (abs(spre) > delta) and (abs(fcur) < abs(fpre)):
            if xpre == xblk:
                stry = -fcur * (xcur - xpre) / (fcur - xpre)
            else:
                dpre = (fpre - fcur) / (xpre - xcur)
                dblk = (fblk - fcur) / (xblk - xcur)
                stry = -fcur * (fblk - fpre) / (fblk * dpre - fpre * dblk)

            if 2 * abs(stry) < min(abs(spre), 3 * abs(sbis) - delta):
                # accept step
                spre = scur
                scur = stry
            else:
                # bisect
                spre = sbis
                scur = sbis
        else:
            # bisect
            spre = sbis
            scur = sbis
        xpre = xcur
        fpre = fcur
        if abs(scur) > delta:
            xcur += scur
        elif sbis > 0:
            xcur += delta
        else:
            xcur -= delta

        fcur = f_root(xcur, *args)
        hc = xcur
    return hc


def group_icons(groupsize):
    """
    Return a fontawesome icon id corresponding to group size.

    Parameters
    ----------
    groupsize : float
        size of group [m]

    Returns
    -------
    icon : str
        identifier for groupsize fontawesome icon
    """
    if groupsize < 1.0e-2:
        icon = "fa-solid fa-spider"
    elif groupsize < 2.5e-2:
        icon = "fa-solid fa-eye"
    elif groupsize < 3.5e-2:
        icon = "fa-solid fa-egg"
    elif groupsize < 5.0e-2:
        icon = "fa-regular fa-lightbulb"
    elif groupsize < 8.0e-2:
        icon = "fa-solid fa-apple-whole"
    elif groupsize < 23.0e-2:
        icon = "fa-solid fa-volleyball"
    elif groupsize < 27.5e-2:
        icon = "fa-solid fa-basketball"
    elif groupsize < 35.0e-2:
        icon = "fa-solid fa-record-vinyl"
    elif groupsize < 45.0e-2:
        icon = "fa-solid fa-hat-wizard"
    elif groupsize < 55.0e-2:
        icon = "fa-solid fa-guitar"
    elif groupsize < 75.0e-2:
        icon = "fa-brands fa-linux"
    elif groupsize < 122.0e-2:
        icon = "fa-solid fa-bullseye"
    elif groupsize < 180.0e-2:
        icon = "fa-solid fa-car"
    else:
        icon = "fa-solid fa-earth-americas"

    return icon
