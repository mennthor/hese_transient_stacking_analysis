# coding: utf-8

"""
Use runlists to build a JSON file with the needed source information and to
which sample each on belongs to.
"""

import os
import json
from glob import glob
import gzip
import numpy as np
import astropy.time as astrotime

from _paths import PATHS
from _loader import runlist_loader


src_path = os.path.join(PATHS.local, "hese_scan_maps")
runlist_path = os.path.join(PATHS.local, "runlists")

outpath = os.path.join(PATHS.local, "source_list")
if not os.path.isdir(outpath):
    os.makedirs(outpath)

# Load runlists
runlists = runlist_loader("all")

# Load sources up to HESE 6yr, list from:
#   https://wiki.icecube.wisc.edu/index.php/Analysis_of_pre-public_alert_HESE/EHE_events#HESE
# Last Run ID is 127853 from late 86V (2015) run, next from 7yr is 128290
src_files = sorted(glob(os.path.join(src_path, "*.json.gz")))

sources = []
for src_file in src_files:
    with gzip.open(src_file) as _f:
        src_dict = json.load(_f)
        # Build a compact version with all relevant infos
        src_i = {}
        for key in ["run_id", "event_id", "mjd"]:
            src_i[key] = src_dict[key]
        # Store best fit from direct local trafo and map maximum
        src_i["ra"] = src_dict["bf_equ"]["ra"]
        src_i["dec"] = src_dict["bf_equ"]["dec"]
        src_i["ra_map"] = src_dict["bf_equ_pix"]["ra"]
        src_i["dec_map"] = src_dict["bf_equ_pix"]["dec"]
        # Also store the path to the original file which contains the skymap
        src_i["map_path"] = src_file
        sources.append(src_i)
        print("Loaded HESE source from run {}:\n  {}".format(
            src_i["run_id"], src_file))

print("Number of considered sources: {}".format(len(src_files)))
sources = np.array(sources)

# Match sources with their seasons and store to JSON
# We could just copy the list from the wiki here, but let's just check with
# the runlists
sources_per_sam = {}
src_t = np.array([src_["mjd"] for src_ in sources])
for name, runs in runlists.items():
    print("Match sources for sample {}".format(name))
    tmin = np.amin([astrotime.Time(r["good_tstart"]).mjd for r in runs])
    tmax = np.amax([astrotime.Time(r["good_tstop"]).mjd for r in runs])
    t_mask = (src_t >= tmin) & (src_t <= tmax)
    # Store all sources for the current sample
    sources_per_sam[name] = sources[t_mask].tolist()
    print("  {} sources in this sample.".format(np.sum(t_mask)))
assert sum(map(len, sources_per_sam.values())) == len(sources)

with open(os.path.join(outpath, "source_list.json"), "w") as outf:
    json.dump(sources_per_sam, fp=outf, indent=2)
