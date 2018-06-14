# coding: utf-8

"""
Create jobfiles for `09-performance.py`

Arguments:
--sig_inj=ps
    - Make 'perfect' trials, injecting where we test.
--sig_inj=healpy
    - Make 'effective' trials, injecting from the source priors but still
      testing at the best fit positions.

##############################################################################
# Used seed range for performance trial jobs: [200000, 300000)
##############################################################################
"""

import os
import numpy as np
import argparse

from dagman import dagman
from _paths import PATHS
from _loader import time_window_loader


MIN_SEED, MAX_SEED = 200000, 300000

parser = argparse.ArgumentParser(description="hese_stacking")
parser.add_argument("--sig_inj", type=str, required=True)
parser.add_argument("--skylab_mc", action="store_true")
args = parser.parse_args()
sig_inj_type = args.sig_inj
skylab_mc = args.skylab_mc

if sig_inj_type not in ["ps", "healpy"]:
    raise ValueError("`sig_inj_type` can be 'ps' or 'healpy'.")
if skylab_mc:
    print("# Using full skylab MC")
    mc_info = "_skylab_MC"
else:
    mc_info = ""

# Make jobs
print("Preparing job files for injector type: '{}'".format(sig_inj_type))
job_creator = dagman.DAGManJobCreator(mem=3)
job_name = "hese_transient_stacking"

job_dir = os.path.join(PATHS.jobs,
                       "performance_trials_" + sig_inj_type + mc_info)
script = os.path.join(PATHS.repo, "09-performance.py")

# Get time windows
all_tw_ids = time_window_loader()
n_time_windows = len(all_tw_ids)

# Performance trials don't need long because we only need some 10k trials
ntrials = 20000
njobs_per_tw = 1
ntrials_per_job = int(ntrials / float(njobs_per_tw))
n_jobs_tot = njobs_per_tw * n_time_windows
if int(ntrials) != ntrials_per_job * njobs_per_tw:
    raise ValueError("Job settings does not lead to exactly " +
                     "{} trials".format(int(ntrials)))
print("Preparing {} trials per batch per time window".format(int(ntrials)))
print("  - {} jobs per time window".format(njobs_per_tw))
print("  - {} trials per job".format(ntrials_per_job))
print("Creating {} total jobfiles for all time windows".format(int(n_jobs_tot)))

# tw_ids: 00, ..., 00, 01, .., 01, ..., 20, ..., 20
tw_ids = np.concatenate([njobs_per_tw * [tw_id] for tw_id in all_tw_ids])

job_args = {
    "rnd_seed": np.arange(MIN_SEED, MIN_SEED + n_jobs_tot).astype(int),
    "ntrials": n_jobs_tot * [ntrials_per_job],
    "tw_id": tw_ids,
    "sig_inj": n_jobs_tot * [sig_inj_type],
    "skylab_mc": n_jobs_tot * ["__FLAG__"],
    }

if sig_inj_type == "healpy":
    job_args["rnd_seed"] = job_args["rnd_seed"] + n_jobs_tot

if (np.any(job_args["rnd_seed"] < MIN_SEED) or
        np.any(job_args["rnd_seed"] >= MAX_SEED)):
    raise RuntimeError("Used a seed outside the allowed range!")

job_creator.create_job(script=script, job_args=job_args,
                       job_name=job_name, job_dir=job_dir, overwrite=True)
