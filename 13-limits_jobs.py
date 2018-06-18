# coding: utf-8

"""
Create jobfiles for `13-limits.py`

##############################################################################
# Used seed range for performance trial jobs: [500000, 600000)
##############################################################################
"""

import os
import numpy as np

from dagman import dagman
from _paths import PATHS
from _loader import time_window_loader


MIN_SEED, MAX_SEED = 500000, 600000

# Make jobs
print("Preparing job files for limit trials")
job_creator = dagman.DAGManJobCreator(mem=3)
job_name = "hese_transient_stacking"

job_dir = os.path.join(PATHS.jobs, "limits_healpy")
script = os.path.join(PATHS.repo, "13-limits.py")

# Get time windows
all_tw_ids = time_window_loader()
n_time_windows = len(all_tw_ids)

# Set the scanned gamma grid
gammas = np.arange(1.5, 3.6, 0.1)
n_gammas = len(gammas)

# 1 job for each time window and energy range, doing 'ntrials' trials per batch
n_trials_per_job = 20000
n_jobs_per_tw = n_gammas
n_jobs_tot = n_jobs_per_tw * n_time_windows
print("Preparing {} trials per batch per gamma per time window".format(
    int(n_trials_per_job)))
print("  - {} jobs per time window".format(n_jobs_per_tw))
print("Creating {} total jobfiles for all time windows".format(int(n_jobs_tot)))

# tw_ids: 00, ..., 00, 01, .., 01, ..., 20, ..., 20
tw_ids = np.concatenate([n_jobs_per_tw * [tw_id] for tw_id in all_tw_ids])

# gammas: [gammas, gammas, ..., gammas]
gammas = np.tile(gammas, reps=n_time_windows)

job_args = {
    "ntrials": n_jobs_tot * [n_trials_per_job],
    "tw_id": tw_ids,
    "gamma": gammas,
    "rnd_seed": np.arange(MIN_SEED, MIN_SEED + n_jobs_tot).astype(int),
    }

if (np.any(job_args["rnd_seed"] < MIN_SEED) or
        np.any(job_args["rnd_seed"] >= MAX_SEED)):
    raise RuntimeError("Used a seed outside the allowed range!")

job_creator.create_job(script=script, job_args=job_args,
                       job_name=job_name, job_dir=job_dir, overwrite=True)
