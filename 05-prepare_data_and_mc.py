# coding: utf-8

"""
1) Data events outside the earliest / latest runs per sample are removed,
   because they don't contribute anyway here, because here the runlists were
   constructed non-overlapping.
2) Split analysis datasets into off and ontime time data for trial handling.
   The largest tested source window is split off as on-time data, the rest is
   kept as off-data to build models and injectors from.
3) Remove HESE like events identified in `04-check_hese_mc_ids` from the
   simulation files.
"""

import os
import json
import gzip
import numpy as np
from astropy.time import Time as astrotime

from skylab.datasets import Datasets

from _paths import PATHS
from _loader import source_list_loader, time_window_loader, runlist_loader
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
    is_hese_like : array-like, shape (len(mc),)
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
    is_hese_like = np.isin(combined_mcids, combined_heseids)
    print("  Found {} / {} HESE like events in MC".format(np.sum(is_hese_like),
                                                          len(mc)))
    return is_hese_like


def split_data_on_off(ev_t, src_dicts, dt0, dt1):
    """
    Returns a mask to split experimental data in on and off source regions.

    Parameters
    ----------
    ev_t : array-like
        Experimental times in MJD days.
    src_dicts : list of dicts
        One dict per source, must have key ``'mjd'``.
    dt0 : float
        Left border of ontime window for all sources in seconds relative to the
        source times, should be negative for earlier times.
    dt1 : float
        Right border of ontime window for all sources in seconds relative to the
        source times.

    Returns
    -------
    offtime : array-like, shape (len(exp),)
        Mask: ``True`` when event in ``exp`` is in the off data region.
    """
    SECINDAY = 24. * 60. * 60.
    nevts, nsrcs = len(ev_t), len(src_dicts)

    dt0_mjd = np.empty(nsrcs, dtype=float)
    dt1_mjd = np.empty(nsrcs, dtype=float)
    for i, src in enumerate(src_dicts):
        dt0_mjd[i] = src["mjd"] + dt0 / SECINDAY
        dt1_mjd[i] = src["mjd"] + dt1 / SECINDAY

    # Broadcast to test every source at once
    ev_t = np.atleast_1d(ev_t)[None, :]
    dt0_mjd, dt1_mjd = dt0_mjd[:, None], dt1_mjd[:, None]

    ontime = np.logical_and(ev_t >= dt0_mjd, ev_t <= dt1_mjd)
    offtime = np.logical_not(np.any(ontime, axis=0))
    assert np.sum(np.any(ontime, axis=0)) + np.sum(offtime) == nevts

    print("  Ontime window duration: {:.2f} sec".format(dt1 - dt0))
    print("  Ontime events: {} / {}".format(np.sum(ontime), nevts))
    for i, on_per_src in enumerate(ontime):
        print("  - Source {}: {} on time".format(i, np.sum(on_per_src)))
    return offtime


off_data_outpath = os.path.join(PATHS.data, "data_offtime")
on_data_outpath = os.path.join(PATHS.data, "data_ontime")
mc_outpath = os.path.join(PATHS.data, "mc_no_hese")
for _p in [off_data_outpath, on_data_outpath, mc_outpath]:
    if not os.path.isdir(_p):
        os.makedirs(_p)

# Load sources and lowest/highest lower/upper time window edge
sources = source_list_loader("all")
_dts0, _dts1 = time_window_loader("all")
dt0_min, dt1_max = np.amin(_dts0), np.amax(_dts1)

# Load runlists
runlists = runlist_loader("all")

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

    name = name.replace(", ", "_")

    # Remove events before first and after last run per sample
    first_run = min(map(lambda d: astrotime(d["good_tstart"],
                                            format="iso").mjd, runlists[name]))
    last_run = max(map(lambda d: astrotime(d["good_tstop"],
                                           format="iso").mjd, runlists[name]))
    is_inside_runs = (exp["time"] >= first_run) & (exp["time"] <= last_run)
    print("  Removing {} / {} events outside runs.".format(
        np.sum(~is_inside_runs), len(exp)))
    exp = exp[is_inside_runs]

    # Split data in on and off parts with the largest time window
    is_offtime = split_data_on_off(exp["time"], sources[name], dt0_min, dt1_max)

    # Remove HESE like events from MC
    _fname = os.path.join(PATHS.local, "check_hese_mc_ids",
                          name2heseid_file[name])
    with gzip.open(_fname) as _file:
        heseids = json.load(_file)
        print("  Loaded HESE like MC IDs from :\n    {}".format(_fname))
    is_hese_like = remove_hese_from_mc(mc, heseids)

    # Save, also in npy format
    print("  Saving on, off and non-HESE like MCs at:")
    out_arrs = [exp[is_offtime], exp[~is_offtime], mc[~is_hese_like]]
    for out_path, arr in zip(out_paths, out_arrs):
        _fname = os.path.join(out_path, name + ".npy")
        np.save(file=_fname, arr=arr)
        print("    '{}'".format(_fname))
