
import numpy as np

from archerycalculator.db import query_db, sql_to_dol

from archeryutils import rounds
from archeryutils.handicaps import handicap_equations as hc_eq
from archeryutils.classifications import classifications as class_func

from archerycalculator import TableForm

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

    convert_dict = {"bray_i": "bray_i_compound",
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
    print(round_codenames)
    if notlistflag:
        print(round_codenames[:])
        return round_codenames[0]
    else:
        return round_codenames
