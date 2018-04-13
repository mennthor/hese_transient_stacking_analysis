# coding: utf-8

"""
Make rundicts from official runlists and data selection as stated on the
analysis wikis.

Datasets are loaded from the skylab dataset module, along with the official run
selection.
"""

import os
import json
import numpy as np
import astropy.time as astrotime

from skylab.datasets import Datasets

from _paths import PATHS
from myi3scripts import arr2str


def make_run_list(ev_times, ev_runids, exclude_runs=None):
    """
    Make a run list from given event times and run IDs and a list of included
    runs. Run start, stop are estimated from first and last event time in each
    run, which is biased but there seems to be no better way.

    Parameters
    ----------
    ev_times : array-like, shape (nevts,)
        Event times in MJD days from the used data sample.
    ev_runids : array-like, shape (nevts,)
        Event run IDs from the used data sample.
    exclude_runs : array-like or None, optional
        Run IDs to exclude, for example when samples overlap.
        (default: ``None``)

    Returns
    -------
    run_list : list of dicts
        Dict with keys similar to a snapshot from [1]_ in JSON format:
            [
              {"good_tstart": "YYYY-MM-DD HH:MM:SS",
               "good_tstop": "YYYY-MM-DD HH:MM:SS",
               "run": 123456},
              {...}, ..., {...}
            ]
        Times are given in iso formatted strings and run IDs as integers.

    References
    ----------
    .. [1] live.icecube.wisc.edu/snapshots
    """
    # If selected runs were empty on final level, they are not considered here
    used_run_ids = np.unique(ev_runids).astype(int)
    ev_runids = ev_runids.astype(int)

    if exclude_runs is not None:
        used_run_ids = filter(lambda runid: runid not in exclude_runs,
                              used_run_ids)
        print("  Exluded runs: {}".format(arr2str(exclude_runs, fmt="{:d}")))

    run_list = []
    livetimes = np.zeros(len(used_run_ids), dtype=float)
    for i, runid in enumerate(used_run_ids):
        ev_mask = (ev_runids == runid)
        ev_t = ev_times[ev_mask]
        # (Under-) Estimate livetime by difference of last and first event time
        tstart = astrotime.Time(np.amin(ev_t), format="mjd").iso
        tstop = astrotime.Time(np.amax(ev_t), format="mjd").iso
        livetimes[i] = np.amax(ev_t) - np.amin(ev_t)
        # Append run dict to run list
        run_list.append(
            {"run": runid, "good_tstart": tstart, "good_tstop": tstop})

    print("  Livetime: {:.3f} days".format(np.sum(livetimes[livetimes > 0])))
    print("  Selected {} / {} runs with livetime > 0.".format(
        np.sum(livetimes > 0), len(used_run_ids)))
    return run_list


# Load PS track and GFU data from skylab as record arrays for the 6 years of
# HESE sources that are analysed here
ps_tracks = Datasets["PointSourceTracks"]
ps_sample_names = ["IC79", "IC86, 2011", "IC86, 2012-2014"]
gfu_tracks = Datasets["GFU"]
gfu_sample_names = ["IC86, 2015"]
all_sample_names = sorted(ps_sample_names + gfu_sample_names)

# Exclude some runs that are overlapping in the samples. If we don't then
# sources get matched to multiple samples (which could be manually avoided, but
# let's just remove the few runs here)
exclude = {name: None for name in all_sample_names}
exclude["IC86, 2012-2014"] = [120028, 120029, 120030]
exclude["IC86, 2015"] = [126289, 126290, 126291]

outpath = os.path.join(PATHS.local, "runlists")
if not os.path.isdir(outpath):
    os.makedirs(outpath)

for name in all_sample_names:
    print("Making runlist for {}".format(name))
    if name in ps_sample_names:
        tracks = ps_tracks
    else:
        tracks = gfu_tracks

    exp_files = tracks.files(name)[0]
    exp = tracks.load(exp_files)

    _info = arr2str(exp_files if isinstance(exp_files, list) else [exp_files],
                    sep="\n    ")
    print("  Loaded {} track sample from skylab:\n    {}".format(
        "PS" if name in ps_sample_names else "GFU", _info))

    ev_times, ev_runids = exp["time"], exp["Run"]
    run_list = make_run_list(ev_times, ev_runids, exclude[name])
    fname = name.replace(", ", "_") + ".json"
    with open(os.path.join(outpath, fname), "w") as outf:
        json.dump(run_list, fp=outf, indent=2)
        print("  Saved to:\n    {}".format(os.path.join(outpath, fname)))
