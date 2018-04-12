# coding: utf-8

"""
1) Split analysis datasets into off and ontime time data for trial handling.
   The largest tested source window is split off as on-time data, the rest is
   kept as off-data to build models and injectors from.
2) Remove HESE like events identified in `04-check_hese_mc_ids` from the
   simulation files.
"""

import os
import json
import gzip
import numpy as np

from skylab.datasets import Datasets

from _paths import PATHS
from _loader import source_list_loader, time_window_loader
from myi3scripts import arr2str


def remove_hese_from_mc(mc, heseids):
    """
    Mask all values in ``mc`` that have the same run and event ID combination
    as in ``heseids``.

    Parameters
    ----------
    mc : record-array
        Needs names ``'Run', 'Event'``.
    heseids : dict or record-array
        Needs names / keys ``'run_id', 'event_id``.

    Returns
    -------
    is_hese_mask : array-like, shape (len(mc),)
        Mask: ``True`` if for each event in ``mc`` that is HESE like.
    """
    # Make combined IDs to easily match against HESE IDs with `np.isin`
    factor_mc = 10**np.ceil(np.log10(np.amax(mc["Event"])))
    _evids = np.atleast_1d(heseids["event_id"])
    factor_hese = 10**np.ceil(np.log10(np.amax(_evids)))
    factor = max(factor_mc, factor_hese)

    combined_mcids = (factor * mc["Run"] + mc["Event"]).astype(int)
    assert np.all(combined_mcids > factor)  # Is int overflow a thing here?

    _runids = np.atleast_1d(heseids["run_id"])
    combined_heseids = (factor * _runids + _evids).astype(int)
    assert np.all(combined_heseids > factor)

    # Check which MC event is tagged as HESE like
    is_hese_mask = np.isin(combined_mcids, combined_heseids)
    print("  Found {} / {} HESE like events in MC".format(np.sum(is_hese_mask),
                                                          len(mc)))
    return is_hese_mask


def split_data_on_off(ev_t, dt0, dt1):
    """
    Returns a mask to split experimental data in on and off source regions.

    Parameters
    ----------
    ev_t : array-like
        Experimental times in MJD days.
    dt0 : array-like
        Absolute left borders of time window for each source in MJD days.
    dt1 : array-like
        Absolute right borders of time window for each source in MJD days.

    Returns
    -------
    is_off_data : array-like, shape (len(exp),)
        Mask: ``True`` when event in ``exp`` is in the off data region.
    """
    # Broadcast to test every source at once
    ev_t = np.atleast_1d(ev_t)[None, :]
    dt0, dt1 = np.atleast_1d(dt0)[:, None], np.atleast_1d(dt1)[:, None]

    is_on_data = (ev_t >= dt0) & (ev_t <= dt1)
    is_off_data = np.logical_not(np.any(is_on_data, axis=0))
    assert np.sum(np.any(is_on_data, axis=0)) + np.sum(is_off_data) == (
        ev_t.shape[1])

    print("  On time events: {} / {}".format(np.sum(is_on_data), ev_t.shape[1]))
    for i, ontime in enumerate(is_on_data):
        print("  - Source {}: {} on time".format(i, np.sum(ontime)))
    return is_off_data


def make_src_dts_from_dict_list(dict_list, dt0, dt1):
    """
    Makes arrays ``dt0``, ``dt1`` with start, stop of each sources time window
    in MJD days to split off data.

    Parameters
    ----------
    dict_list : list of dict
        One dict per source, must have key ``'mjd'``.
    dt0 : float
        Left border of time window for all sources in seconds relative to the
        source times, should be negative for earlier times.
    dt1 : float
        Right border of time window for all sources in seconds relative to the
        source times.

    Returns
    -------
    dt0, dt1 : array-like
        Left and right borders in absolute MJD for each source from the list.
    """
    SECINDAY = 24. * 60. * 60.
    dt0 /= SECINDAY
    dt1 /= SECINDAY

    dt0_mjd, dt1_mjd = [], []
    for src in dict_list:
        dt0_mjd.append(src["mjd"] + dt0)
        dt1_mjd.append(src["mjd"] + dt1)

    return np.array(dt0_mjd), np.array(dt1_mjd)


off_data_outpath = os.path.join(PATHS.data, "data_offtime")
on_data_outpath = os.path.join(PATHS.data, "data_ontime")
mc_outpath = os.path.join(PATHS.data, "mc_no_hese")
for _p in [off_data_outpath, on_data_outpath, mc_outpath]:
    if not os.path.isdir(_p):
        os.makedirs(_p)

# Load sources and time windows
sources = source_list_loader("all")
_dt0, _dt1 = time_window_loader("all")
dt0_max, dt1_max = np.amax(_dt0), np.amax(_dt1)

# Load needed data and MC from PS track and add in one year of GFU sample
ps_tracks = Datasets["PointSourceTracks"]
ps_sample_names = ["IC79", "IC86, 2011", "IC86, 2012-2014"]
gfu_tracks = Datasets["GFU"]
gfu_sample_names = ["IC86, 2015"]
all_sample_names = sorted(ps_sample_names + gfu_sample_names)

# Base MC is same for multiple samples, match names here
name2heseid_file = {
    "IC79": "IC79.json.gz",
    "IC86_2011": "IC86_2011.json.gz",
    "IC86_2012-2014": "IC86_2012-2015.json.gz",
    "IC86_2015": "IC86_2012-2015.json.gz"
}

out_paths = [off_data_outpath, on_data_outpath, mc_outpath]
for name in all_sample_names:
    print("Working with sample {}".format(name))

    if name in ps_sample_names:
        tracks = ps_tracks
    else:
        tracks = gfu_tracks

    exp_file, mc_file = tracks.files(name)
    exp = tracks.load(exp_file)
    mc = tracks.load(mc_file)

    print("  Loaded {} track sample from skylab:".format(
        "PS" if name in ps_sample_names else "GFU"))
    _info = arr2str(exp_file if isinstance(exp_file, list) else [exp_file],
                    sep="\n    ")
    print("    Data:\n      {}".format(_info))
    print("    MC  :\n      {}".format(mc_file))

    # Split data in on and off parts
    name = name.replace(", ", "_")
    dt0_mjd, dt1_mjd = make_src_dts_from_dict_list(sources[name],
                                                   dt0_max, dt1_max)
    is_off_data = split_data_on_off(exp["time"], dt0_mjd, dt1_mjd)

    # Remove HESE like events from MC
    _fname = os.path.join(PATHS.local, "check_hese_mc_ids",
                          name2heseid_file[name])
    with gzip.open(_fname) as _file:
        heseids = json.load(_file)
        print("  Loaded HESE like MC IDs from :\n    {}".format(_fname))
    is_hese_mask = remove_hese_from_mc(mc, heseids)

    # Save, also in npy format
    print("  Saving on, off and non-HESE like MCs at:")
    out_arrs = [exp[is_off_data], exp[~is_off_data], mc[~is_hese_mask]]
    for out_path, arr in zip(out_paths, out_arrs):
        _fname = os.path.join(out_path, name + ".npy")
        np.save(file=_fname, arr=arr)
        print("    '{}'".format(_fname))
