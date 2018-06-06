# coding: utf-8

"""
Combine output for each post trial job output.
"""

import os
import sys
import json
import gzip
from glob import glob

try:
    from tqdm import tqdm
except ImportError:
    print("If you want fancy status bars: `pip install --user tqdm` ;)")
    tqdm = iter

from _paths import PATHS


inpath = os.path.join(PATHS.data, "post_trials")

outpath = os.path.join(PATHS.local, "post_trials_combined")
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

files = sorted(glob(os.path.join(inpath, "job_*.json.gz")))
if len(files) > 0:
    print("Found {} post trial files".format(len(files)))
    # Build output dict
    trials = {
        "ns": [],
        "ts": [],
        "rnd_seed": [],
        "ntrials": 0,
        "ntrials_per_batch": [],
        }
    # Concatenate all files
    for _file in tqdm(files):
        with gzip.open(_file) as infile:
            trial_i = json.load(infile)
        trials["ns"] += trial_i["ns"]
        trials["ts"] += trial_i["ts"]
        trials["ntrials"] += trial_i["ntrials"]
        trials["rnd_seed"].append(trial_i["rnd_seed"])
        trials["ntrials_per_batch"].append(trial_i["ntrials"])
    trials["time_windows"] = trial_i["time_windows"]
    # Save it
    fpath = os.path.join(outpath, "post_trials.json.gz")
    print("- Saving to:\n    {}".format(fpath))
    with gzip.open(fpath, "w") as outf:
        json.dump(trials, fp=outf, indent=0, separators=(",", ":"))
else:
    print("  No trials found, exiting.")

print("- Done")
