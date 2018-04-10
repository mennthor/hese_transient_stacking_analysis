# coding: utf-8

"""
1) Split analysis datasets into off and ontime time data for trial handling.
2) Remove HESE like events identified in `03-check_hese_mc_ids` from the
   simulation files.
"""

import os
import json
import numpy as np
import astropy.time as astrotime

from skylab.datasets import Datasets


inpath = os.path.join("/home", "tmenne", "analysis",
                      "hese_transient_stacking_analysis")
outpath = os.path.join("/data", "user", "tmenne",
                       "hese_transient_stacking_analysis")

# Load needed data and MC from PS track and add in one year of GFU sample
ps_tracks = Datasets["PointSourceTracks"]
ps_sample_names = ["IC79", "IC86, 2011", "IC86, 2012",
                   "IC86, 2013", "IC86, 2014"]

gfu_tracks = Datasets["GFU"]
gfu_sample_names = ["IC86, 2015"]

for name in sample_names:
    print("Working with sample {}".format(name))
    exp_file, mc_file = pstracks.files(name)

    print("  Loading PS track sample from skylab:")
    print("    Data: {}".format(exp_file))
    exp = pstracks.load(exp_file)

    print("    MC  : {}".format(mc_file))
    mc = pstracks.load(mc_file)

    # Get prepared runtime list and sources
    _fname = os.path.join(inpath, "out", "runlists", name.replace(", ", "_"))
    with open(_fname) as _file:
        runlist = json.load(_file)
        print("  Loaded runlist: {}".format(_fname))

# ###### Get prepared run time lists
# rundict = {}

# rundict["79"] = json.load(open(os.path.join(PATH,
#                                             "goodruns/IC79v24.json")))
# rundict["86I"] = json.load(open(os.path.join(PATH,
#                                              "goodruns/IC86_2011.json")))
# rundict["86II"] = json.load(open(os.path.join(PATH,
#                                               "goodruns/IC86_2012.json")))
# rundict["86III"] = json.load(open(os.path.join(PATH,
#                                                "goodruns/IC86_2013.json")))

# print("Loaded goodrun dicts from: " + PATH + "/goddruns")


# ###### Load HESE tracks locations
path = os.path.join(PATH,
                    "public_data_release/All_HESE_Events_4_years_tracks.txt")
src_t = np.loadtxt(path, usecols=[1], unpack=True)

srcs_t = {}
for key, rl in rundict.items():
    runs = rl["runs"]
    tmin = np.amin([astrotime(r["good_tstart"]).mjd for r in runs])
    tmax = np.amax([astrotime(r["good_tstop"]).mjd for r in runs])
    t_mask = (src_t >= tmin) & (src_t <= tmax)

    srcs_t[key] = src_t[t_mask]

print("Made HESE srcs from: " + path)
print("Times are:")
for key, ti in srcs_t.items():
    print(key)
    for tii in ti:
        print("  {:.2f} MJD".format(tii))


# ###### Setup time window for all srcs
PATH = "/home/tmenne/analysis/HESE_transients/res/time_windows/time_windows.txt"
dt_max = np.loadtxt(fname=PATH)[-1]

print("Loaded longest time window: {:.1f}s".format(np.diff(dt_max)[0]))


# ###### Split off time data
PATH = ("/home/tmenne/analysis/HESE_transients/res/" +
        "llh_settings/llh_settings.json")
with open(PATH, "r") as f:
    llh_args = json.load(f)
time_pdf_args = llh_args["time"]
print("Read LLH time settings from:\n" + PATH)
print(time_pdf_args)

tranges = {}
for key, ti in srcs_t.items():
    dti = np.repeat([dt_max], repeats=len(ti), axis=0)
    tranges[key] = LLH.GRBLLH.get_on_time_windows(ti, dti, time_pdf_args)


# ###### Remove the ontime part in wich the time PDFs are defined to be non-zero
# from the whole data set and use the offtime sets for PDF construction.
PATH = "/home/tmenne/nobackup/PS7yr_npz/offdata"
if not os.path.isdir(PATH):
    os.makedirs(PATH)

for key, trange in tranges.items():
    t = exp[key]["timeMJD"][None, :]
    ontime = (t >= trange[:, [0]]) & (t <= trange[:, [1]])
    offtime = np.logical_not(np.any(ontime, axis=0))
    exp_off = exp[key][offtime]

    pi = os.path.join(PATH, key + ".npy")
    print("Saving '{}' offdata to:\n  {}".format(key, pi))
    np.save(arr=exp_off, file=pi)

print("Done!")




outpath = os.path.join("/home", "tmenne", "analysis",
                       "hese_transient_stacking_analysis", "out",
                       "runlists")
if not os.path.isdir(outpath):
    os.makedirs(outpath)
