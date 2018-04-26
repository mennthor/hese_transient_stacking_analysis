# coding: utf-8

"""
Create jobfiles for `09-perfromance.py`

##############################################################################
# Used seed range for performance trial jobs: [200000, 201000]
##############################################################################
"""

import os
import numpy as np

from dagman import dagman
from _paths import PATHS
from _loader import time_window_loader


job_creator = dagman.DAGManJobCreator(mem=3)
job_name = "hese_transient_stacking"

job_dir = os.path.join(PATHS.jobs, "performance_trials")
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

job_args = {
    "rnd_seed": np.arange(200000, 200000 + njobs_tot).astype(int),
    "ntrials": njobs_tot * [ntrials_per_job],
    "tw_id": tw_ids,
    }

job_creator.create_job(script=script, job_args=job_args,
                       job_name=job_name, job_dir=job_dir, overwrite=True)
