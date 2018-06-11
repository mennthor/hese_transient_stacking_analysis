# coding: utf-8

"""
Combine output for each time window for all energy ranges to a single file
containing all trials per time window .

Arguments:
--sig_inj=*
    - ps : Select 'ps' type trials to combine.
    - healpy : Select 'healpy' type trials to combine.

--model=*
    - none : Select standard power law as stored in settings.
    TODO: Select performances for actual models
"""

import os
import sys
import json
import gzip
import argparse
from glob import glob

try:
    from tqdm import tqdm
except ImportError:
    print("If you want fancy status bars: `pip install --user tqdm` ;)")
    tqdm = iter

from _paths import PATHS
from _loader import time_window_loader


parser = argparse.ArgumentParser(description="hese_stacking")
parser.add_argument("--sig_inj", type=str, required=True)
parser.add_argument("--model", type=str, required=False, default="none")
args = parser.parse_args()
sig_inj_type = args.sig_inj
model = args.model

if sig_inj_type not in ["ps", "healpy"]:
    raise ValueError("`sig_inj_type` can be 'ps' or 'healpy'.")

if model not in ["none", ]:
    raise ValueError("`model` can be 'none' only at the moment.")

# TODO: Model selection in the job script and use it for the out folder
inpath = os.path.join(PATHS.data, "differential_perf_trials_" + sig_inj_type)

outpath = os.path.join(
    PATHS.data, "differential_perf_trials_" + sig_inj_type + "_combined")
if os.path.isdir(outpath):
    res = raw_input("'{}' already exists. ".format(outpath) +
                    "\nAllow overwrites (y/n)? ")
    if not res.lower() in ("y", "yes"):
        print("Abort. Script has done nothing.")
        sys.exit()
    print("  Using output directory '{}'.".format(outpath))
else:
    os.makedirs(outpath)
    print("Created output directory '{}'.".format(outpath))

# Collect for all time windows
dt0s, dt1s = time_window_loader("all")
for tw_id, (dt0, dt1) in enumerate(zip(dt0s, dt1s)):
    file_path = os.path.join(inpath, "tw_{:02d}_*.json.gz".format(tw_id))
    files = sorted(glob(file_path))
    print("Time window {:02d}, found {} trial files:".format(tw_id, len(files)))
    if len(files) > 0:
        print("  {}\n  ...\n  {}".format(files[0], files[-1]))
        # Build output dict
        trials = {
            "ts": [],
            "mus": None,
            "log_E_bins": None,
            "time_window": [dt0, dt1],
            "time_window_id": tw_id,
            "log_E_bins": [],
            }
        # Concatenate all files
        for _file in tqdm(files):
            with gzip.open(_file) as infile:
                trial_i = json.load(infile)
            trials["ts"].append(trial_i["ts"])
            trials["log_E_bins"] += [trial_i["log_E_nu_lo"],
                                     trial_i["log_E_nu_hi"]]
        trials["mus"] = trial_i["mus"]
        trials["log_E_bins"] = sorted(list(set(trials["log_E_bins"])))
        # Save it
        fpath = os.path.join(outpath, "tw_{:02d}.json.gz".format(tw_id))
        with gzip.open(fpath, "w") as outf:
            json.dump(trials, fp=outf, indent=0, separators=(",", ":"))
            print("  - Saved to:\n    {}".format(fpath))
    else:
        print("  - no trials found")
