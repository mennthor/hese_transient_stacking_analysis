# coding: utf-8

"""
Loader methods for used data formats. If a format changes, we only need to
change the loading part here once.
"""

import os as _os
import json as _json
import numpy as _np
from glob import glob as _glob

from myi3scripts import arr2str as _arr2str

from _paths import PATHS as _PATHS


def timewindow_loader(idx=None):
    """
    Load time window information.

    Parameters
    ----------
    idx : array-like or int or None
        Which time window to load. If ``None`` all are loaded.

    Returns
    -------
    dt0, dt1 : array-like
        Left and right time window edges in seconds.
    """
    _fname = _os.path.join(_PATHS.local, "time_window_list",
                           "time_window_list.txt")
    dt0, dt1 = _np.loadtxt(_fname, unpack=True, comments="#")
    print("Loaded time window list from:\n  {}".format(_fname))
    if idx is None:
        return dt0, dt1
    else:
        idx = _np.atleast_1d(idx)
        print("Returning indices: {}".format(_arr2str(idx)))
        return dt0[idx], dt1[idx]


def source_list_loader(names=None):
    """
    Load source lists.

    Parameters
    ----------
    names : list of str or None or 'all', optional
        Name(s) of the source(s) to load. If ``None`` returns a list of all
        possible names. If ``'all'``, returns all available sources.
        (default: ``None``)

    Returns
    -------
    sources : dict or list
        Dict with name(s) as key(s) and the source lists as value(s). If
        ``names`` was ``None``, returns a list of possible input names. If
        ``names`` was ``'all'`` returns all available sourc lists in the dict.
    """
    source_file = _os.path.join(_PATHS.local, "source_list", "source_list.json")
    with open(source_file) as _file:
        sources = _json.load(_file)
    source_names = sorted(sources.keys())

    if names is None:
        return source_names
    else:
        if names == "all":
            names = source_names
        elif not isinstance(names, list):
            names = [names]

    print("Loaded source list from:\n  {}".format(source_file))
    print("Returning sources for sample(s): {}".format(_arr2str(names)))
    return {name: sources[name] for name in names}


def runlist_loader(names=None):
    """
    Loads runlist for given sample name.

    Parameters
    ----------
    names : list of str or None or 'all', optional
        Name(s) of the runlist(s) to load. If ``None`` returns a list of all
        possible names. If ``'all'``, returns all available runlists.
        (default: ``None``)

    Returns
    -------
    runlists : dict or list
        Dict with name(s) as key(s) and the runlists as value(s). If ``names``
        was ``None``, returns a list of possible input names. If ``names`` was
        ``'all'`` returns all available runlists in the dict.
    """
    runlist_path = _os.path.join(_PATHS.local, "runlists")
    runlist_files = sorted(_glob(_os.path.join(runlist_path, "*")))
    runlist_names = map(lambda s: _os.path.splitext(_os.path.basename(s))[0],
                        runlist_files)
    if names is None:
        return runlist_names
    else:
        if names == "all":
            names = runlist_names
        elif not isinstance(names, list):
            names = [names]

    runlists = {}
    for name in names:
        idx = runlist_names.index(name)
        _fname = runlist_files[idx]
        with open(_fname) as _file:
            print("Load runlist for sample {} from:\n  {}".format(name, _fname))
            runlists[name] = _json.load(_file)

    return runlists


def settings_loader():
    return


def off_data_loader():
    return


def on_data_loader():
    return


def mc_loader():
    return
