# coding: utf-8

"""
Create jobfiles for `11-differential_perf.py`

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
args = parser.parse_args()
sig_inj_type = args.sig_inj

if sig_inj_type not in ["ps", "healpy"]:
    raise ValueError("`sig_inj_type` can be 'ps' or 'healpy'.")

# Make jobs
print("Preparing job files for injector type: '{}'".format(sig_inj_type))
job_creator = dagman.DAGManJobCreator(mem=3)
job_name = "hese_transient_stacking"

job_dir = os.path.join(PATHS.jobs, "differential_perf_trials_" + sig_inj_type)
script = os.path.join(PATHS.repo, "11-differential_perf.py")

# Get time windows
all_tw_ids = time_window_loader()
n_time_windows = len(all_tw_ids)

# Set log10 energy borders for the signal injector to inject differential in E
dlog_E = 0.5
# [1, 9] covers all used MC sets' true log10 energy ranges
log_E_nu_bins = np.arange(2, 9 + dlog_E, dlog_E)
n_log_E_nu_bins = len(log_E_nu_bins) - 1

# 1 job for each time window and energy range, doing 'ntrials' trials per batch
n_trials_per_job = 20000
n_jobs_per_tw = n_log_E_nu_bins
n_jobs_tot = n_jobs_per_tw * n_time_windows
print("Preparing {} trials per batch per energy per time window".format(
    int(n_trials_per_job)))
print("  - {} jobs per time window".format(n_jobs_per_tw))
print("Creating {} total jobfiles for all time windows".format(int(n_jobs_tot)))

# tw_ids: 00, ..., 00, 01, .., 01, ..., 20, ..., 20
tw_ids = np.concatenate([n_jobs_per_tw * [tw_id] for tw_id in all_tw_ids])

# Bin borders: [log_E_nu_bins, log_E_nu_bins, ..., log_E_nu_bins]
bins_lo = np.tile(log_E_nu_bins[:-1], reps=n_time_windows)
bins_hi = np.tile(log_E_nu_bins[1:], reps=n_time_windows)

job_args = {
    "ntrials": n_jobs_tot * [n_trials_per_job],
    "tw_id": tw_ids,
    "log10_E_nu_lo": bins_lo,
    "log10_E_nu_hi": bins_hi,
    "sig_inj": n_jobs_tot * [sig_inj_type],
    "rnd_seed": np.arange(MIN_SEED, MIN_SEED + n_jobs_tot).astype(int),
    }

if sig_inj_type == "healpy":
    job_args["rnd_seed"] = job_args["rnd_seed"] + n_jobs_tot

if (np.any(job_args["rnd_seed"] < MIN_SEED) or
        np.any(job_args["rnd_seed"] >= MAX_SEED)):
    raise RuntimeError("Used a seed outside the allowed range!")

job_creator.create_job(script=script, job_args=job_args,
                       job_name=job_name, job_dir=job_dir, overwrite=True)
