def check_blacklist(roundlist, age, gender, bowstyle):
    """
    Filter indoor rounds to remove any with compound scoring for the purposes of
    display

    Parameters
    ----------
    roundlist : list
        list of archeryutils round codenames

    Returns
    -------
    list
        filtered version of the input list

    References
    ----------
    """

    blacklist = []

    blacklist.append("wa1440_90_small")
    blacklist.append("wa1440_70_small")
    blacklist.append("wa1440_60_small")

    # Gender
    if gender.lower() in ["male"]:
        blacklist.append("hereford")
        blacklist.append("long_metric_ladies")
        blacklist.append("wa1440_60")
        if age.lower().replace(" ", "") in ["50+"]:
            blacklist.append("metric_i")
        else:
            blacklist.append("wa1440_70")

    if gender.lower() in ["female"]:
        blacklist.append("bristol_i")
        blacklist.append("long_metric_i")
        if age.lower().replace(" ", "") in ["50+"]:
            blacklist.append("metric_ii")
        else:
            blacklist.append("wa1440_60")

    # Age
    if age.lower().replace(" ", "") in ["adult", "50+"]:
        blacklist.append("short_metric_i")
    else:
        blacklist.append("short_metric")

    # Bowstyle
    if bowstyle.lower() in ["compound"]:
        blacklist.append("metric_80_50")
    else:
        blacklist.append("wa720_50_c")

    if bowstyle.lower() in ["barebow"]:
        blacklist.append("metric_122_50")
    else:
        blacklist.append("wa720_50_b")

    saferounds = []
    for roundname in roundlist:
        if roundname not in blacklist:
            saferounds.append(roundname)

    return saferounds


def indoor_display_filter(rounddict):
    """
    Filter indoor rounds to remove any with compound scoring for the purposes of
    display

    Parameters
    ----------
    rounddict : dict
        dict of round data where the archeryutils codename is the key

    Returns
    -------
    list
        list of full round names from filtered version of the input dict

    References
    ----------
    """
    for roundname in list(rounddict.keys()):
        if "compound" in roundname:
            del rounddict[roundname]
    return [rounddict[round_i] for round_i in rounddict]


def get_compound_codename(round_codenames):
    """
    convert any indoor rounds with special compound scoring to the compound format

    Parameters
    ----------
    round_codenames : str or list of str
        list of str round codenames to check

    Returns
    -------
    round_codenames : str or list of str
        list of amended round codenames for compound

    References
    ----------
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
        "wa18": "wa18_compound",
        "wa18_triple": "wa18_compound_triple",
        "wa25": "wa25_compound",
        "wa25_triple": "wa25_compound_triple",
    }

    for i, codename in enumerate(round_codenames):
        if codename in convert_dict:
            round_codenames[i] = convert_dict[codename]
    if notlistflag:
        return round_codenames[0]
    else:
        return round_codenames
