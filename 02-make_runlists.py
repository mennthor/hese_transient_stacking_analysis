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

from skylab import datasets


def make_run_list(ev_times, ev_runids, used_run_ids):
    """
    Make a run list from given event times and run IDs and a list of included
    runs. Run start, stop are estimated from first and last event time in each
    run, which is biased but there seems to be no better way.

    Parameters
    ----------
    ev_times : array-like, shape (nevts,)
        Event times from the used data sample.
    ev_runids : array-like, shape (nevts,)
        Event run IDs from the used data sample.
    used_run_ids : array-like
        Run IDs officially used to create the used data sample.

    Returns
    -------
    run_list : list of dicts
        Dict made from a good run runlist snapshot from [1]_ in JSON format.
        Must be a list of single runs of the following structure

            [{
              "good_tstart": "YYYY-MM-DD HH:MM:SS",
              "good_tstop": "YYYY-MM-DD HH:MM:SS",
              "run": 123456, ...,
              },
             {...}, ..., {...}]

        Each run dict must at least have keys ``'good_tstart'``,
        ``'good_tstop'`` and ``'run'``. Times are given in iso formatted
        strings and run numbers as integers as shown above.
    """
    run_list = []
    dt = 0.
    for runid in used_run_ids:
        ev_mask = (ev_runids == runid)
        ev_t = ev_times[ev_mask]
        # Drop zero runs
        if len(ev_t) > 1:
            tstart = astrotime.Time(np.amin(ev_t), format="mjd").iso
            tstop = astrotime.Time(np.amax(ev_t), format="mjd").iso
            dt += (np.amax(ev_t) - np.amin(ev_t))
            d = {}
            d["run"] = int(runid)
            d["good_tstart"] = tstart
            d["good_tstop"] = tstop
            run_list.append(d.copy())
    print("  Livetime: {:.3f} days".format(dt))
    print("  Selected {} / {} nonzero runs.".format(len(run_list),
                                                    len(used_run_ids)))
    return run_list


if __name__ == "__main__":
    # Load current 7yr PS track data from skylab as record arrays, but only for
    # the 4 year of HESE sources that are analysed here
    pstracks = datasets.PointSourceTracks_v002p01b
    sample_names = ["IC79", "IC86, 2011", "IC86, 2012", "IC86, 2013"]

    outpath = os.path.join("/home", "tmenne", "analysis",
                           "hese_transient_stacking_analysis", "out",
                           "runlists")
    if not os.path.isdir(outpath):
        os.makedirs(outpath)

    for name in sample_names:
        print("Making runlist for {}".format(name))
        used_run_ids = pstracks.coenders_runs(name)
        exp_file = pstracks.files(name)[0]
        print("  Using PS track sample from skylab at:\n  {}".format(exp_file))
        exp = pstracks.load(exp_file)
        ev_times, ev_runids = exp["time"], exp["Run"]
        run_list = make_run_list(ev_times, ev_runids, used_run_ids)
        fname = name.replace(", ", "_") + ".json"
        with open(os.path.join(outpath, fname), "w") as outf:
            json.dump(run_list, fp=outf, indent=2)
            print("  Saved to:\n  {}".format(os.path.join(outpath, fname)))
