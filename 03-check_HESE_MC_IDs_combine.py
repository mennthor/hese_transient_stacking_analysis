# coding:utf-8

"""
Combine output jsons for each sample to a single file containing only the IDs.
"""

from __future__ import division, print_function

import sys
import os
import json
from glob import glob
import gzip
import numpy as np

try:
    from tqdm import tqdm
except ImportError:
    print("If you want fancy status bars: `pip install --user tqdm` ;)")
    tqdm = iter


inpath = os.path.join("/data", "user", "tmenne",
                      "hese_transient_stacking_analysis", "rawout",
                      "check_HESE_MC_IDs")
outpath = os.path.join("/home", "tmenne", "analysis",
                       "hese_transient_stacking_analysis", "out",
                       "check_HESE_MC_IDs")
if os.path.isdir(outpath):
    res = raw_input("'{}' already exists. Allow overwrites? ".format(outpath))
    if not res.lower() in ("y", "yes"):
        print("Abort. Script has done nothing.")
        sys.exit()
    print("  Using output directory '{}'.".format(outpath))
else:
    os.makedirs(outpath)
    print("Created output directory '{}'.".format(outpath))

files = np.array(glob(os.path.join(inpath, "*.json")))
file_names = np.array(map(lambda s: os.path.basename(s), files))
dataset_nums = set(map(lambda s: s.split("_")[0], file_names))

# Combine all to a single JSON file
for num in dataset_nums:
    print("Combining IDs from set '{}':".format(num))
    run_ids = []
    event_ids = []
    _files = files[map(lambda s: s.startswith(num), file_names)]
    for fi in tqdm(_files):
        with open(fi, "r") as inf:
            di = json.load(inf)

        run_ids += di["run_id"]
        event_ids += di["event_id"]

    assert len(run_ids) == len(event_ids)
    print("  Total events filtered: {}".format(len(run_ids)))

    # Save all to compressed JSON
    _outp = os.path.join(outpath, "{}.json.gz".format(num))
    with gzip.open(_outp, "wb") as outf:
        json.dump({"event_id": event_ids, "run_id": run_ids}, outf,
                  indent=1, separators=(",", ": "))
        print("  Saved to file '{}'".format(_outp))

print("Done")
