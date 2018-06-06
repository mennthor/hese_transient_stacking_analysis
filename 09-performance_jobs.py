# coding: utf-8

"""
Create jobfiles for `09-performance.py`

Arguments:
--type=ps
    - Make 'perfect' trials, injecting where we test.
--type=healpy
    - Make 'effective' trials, injecting from the source priors but still
      testing at the best fit positions.

##############################################################################
# Used seed range for performance trial jobs: [200000, 201000]
##############################################################################
"""

import os
import numpy as np
import argparse

from dagman import dagman
from _paths import PATHS
from _loader import time_window_loader


parser = argparse.ArgumentParser(description="hese_stacking")
parser.add_argument("--sig_inj", type=str, required=True)
args = parser.parse_args()
sig_inj_type = args.sig_inj

# Make jobs
print("Preparing job files for injector type: '{}'".format(sig_inj_type))
job_creator = dagman.DAGManJobCreator(mem=3)
job_name = "hese_transient_stacking"

job_dir = os.path.join(PATHS.jobs, "performance_trials_" + sig_inj_type)
script = os.path.join(PATHS.repo, "09-performance.py")

# Get time windows
all_tw_ids = time_window_loader()
ntime_windows = len(all_tw_ids)

# Performance trials don't need long because we only need some 10k trials
ntrials = 20000
njobs_per_tw = 1
ntrials_per_job = int(ntrials / float(njobs_per_tw))
njobs_tot = njobs_per_tw * ntime_windows
if int(ntrials) != ntrials_per_job * njobs_per_tw:
    raise ValueError("Job settings does not lead to exactly " +
                     "{} trials".format(int(ntrials)))
print("Preparing {} total trials per time window".format(int(ntrials)))
print("  - {} jobs per time window".format(njobs_per_tw))
print("  - {} trials per job".format(ntrials_per_job))
print("Creating {} total jobfiles for all time windows".format(int(njobs_tot)))

# tw_ids: 00, ..., 00, 01, .., 01, ..., 20, ..., 20
tw_ids = np.concatenate([njobs_per_tw * [tw_id] for tw_id in all_tw_ids])

if sig_inj_type == "ps":
    job_args = {
        "rnd_seed": np.arange(200000, 200000 + njobs_tot).astype(int),
        "ntrials": njobs_tot * [ntrials_per_job],
        "tw_id": tw_ids,
        "sig_inj": njobs_tot * ["ps"],
        }
elif sig_inj_type == "healpy":
    job_args = {
        "rnd_seed": np.arange(200100, 200100 + njobs_tot).astype(int),
        "ntrials": njobs_tot * [ntrials_per_job],
        "tw_id": tw_ids,
        "sig_inj": njobs_tot * ["healpy"],
        }
else:
    raise ValueError("`sig_inj_type` can be 'ps' or 'healpy'.")

job_creator.create_job(script=script, job_args=job_args,
                       job_name=job_name, job_dir=job_dir, overwrite=True)
