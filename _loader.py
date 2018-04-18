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


def time_window_loader(idx=None):
    """
    Load time window information.

    Parameters
    ----------
    idx : array-like or int or 'all' or ``None``, optional
        Which time window to load. If ``'all'``, all are loaded, if ``None`` a
        list of valid indices is returned, sorted ascending to the largest time
        window. (default: ``None``)

    Returns
    -------
    dt0, dt1 : array-like
        Left and right time window edges in seconds. If ``idx``was ``None`` an
        array of valid indices sorted ascending by total time window length is
        returned.
    """
    fname = _os.path.join(_PATHS.local, "time_window_list",
                          "time_window_list.txt")
    dt0, dt1 = _np.loadtxt(fname, unpack=True, comments="#")
    print("Loaded time window list from:\n  {}".format(fname))
    if idx is None:
        idx = _np.argsort(dt1 - dt0)
        return _np.arange(len(idx))[idx]
    if idx == 'all':
        return dt0, dt1
    else:
        idx = _np.atleast_1d(idx)
        print("  Returning indices: {}".format(_arr2str(idx)))
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
    print("  Returning sources for sample(s): {}".format(_arr2str(names)))
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
    folder = _os.path.join(_PATHS.local, "runlists")
    return _common_loader(names, folder=folder, info="runlist")


def settings_loader(names=None):
    """
    Parameters
    ----------
    names : list of str or None or 'all', optional
        Name(s) of the datasets(s) to load. If ``None`` returns a list of all
        possible names. If ``'all'``, returns all available runlists.
        (default: ``None``)

    Returns
    -------
    offtime_data : dict or list
        Dict with name(s) as key(s) and the offtime data record array(s) as
        value(s). If ``names`` was ``None``, returns a list of possible input
        names. If ``names`` was ``'all'`` returns all available data array(s)
        the dict.
    """
    folder = _os.path.join(_PATHS.local, "settings")
    return _common_loader(names, folder=folder, info="settings")


def off_data_loader(names=None):
    """
    Parameters
    ----------
    names : list of str or None or 'all', optional
        Name(s) of the datasets(s) to load. If ``None`` returns a list of all
        possible names. If ``'all'``, returns all available runlists.
        (default: ``None``)

    Returns
    -------
    offtime_data : dict or list
        Dict with name(s) as key(s) and the offtime data record array(s) as
        value(s). If ``names`` was ``None``, returns a list of possible input
        names. If ``names`` was ``'all'`` returns all available data array(s)
        the dict.
    """
    folder = _os.path.join(_PATHS.data, "data_offtime")
    return _common_loader(names, folder=folder, info="offtime data")


def on_data_loader(names=None):
    """
    Parameters
    ----------
    names : list of str or None or 'all', optional
        Name(s) of the datasets(s) to load. If ``None`` returns a list of all
        possible names. If ``'all'``, returns all available runlists.
        (default: ``None``)

    Returns
    -------
    ontime_data : dict or list
        Dict with name(s) as key(s) and the ontime data record array(s) as
        value(s). If ``names`` was ``None``, returns a list of possible input
        names. If ``names`` was ``'all'`` returns all available data array(s) in
        the dict.
    """
    folder = _os.path.join(_PATHS.data, "data_ontime")
    return _common_loader(names, folder=folder, info="ontime data")


def mc_loader(names=None):
    """
    Parameters
    ----------
    names : list of str or None or 'all', optional
        Name(s) of the datasets(s) to load. If ``None`` returns a list of all
        possible names. If ``'all'``, returns all available runlists.
        (default: ``None``)

    Returns
    -------
    mc : dict or list
        Dict with name(s) as key(s) and the MC record array(s) as value(s). If
        ``names`` was ``None``, returns a list of possible input names. If
        ``names`` was ``'all'`` returns all available MC array(s) in the dict.
    """
    folder = _os.path.join(_PATHS.data, "mc_no_hese")
    return _common_loader(names, folder=folder, info="MC")


def _common_loader(names, folder, info):
    """
    Outsourced some common loader code.

    Parameters
    ----------
    names : list of str, None or 'all'
        See explicit loaders.
    folder : string
        Full path to folder from where to load the data.
    info : str
        Info for print.

    Returns
    -------
    data : dict
        See explicit loader returns.
    """
    files = sorted(_glob(_os.path.join(folder, "*")))
    file_names = map(lambda s: _os.path.splitext(_os.path.basename(s))[0],
                     files)

    if names is None:
        return file_names
    else:
        if names == "all":
            names = file_names
        elif not isinstance(names, list):
            names = [names]

    data = {}
    for name in names:
        idx = file_names.index(name)
        fname = files[idx]
        print("Load {} for sample {} from:\n  {}".format(info, name, fname))
        ext = _os.path.splitext(fname)[1]
        if ext == ".npy":
            data[name] = _np.load(fname)
        elif ext == ".json":
            with open(fname) as json_file:
                data[name] = _json.load(json_file)
        else:
            raise ValueError("Couldn't load unknown datatype: '{}'".format(ext))

    return data
