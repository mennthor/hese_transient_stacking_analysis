# coding: utf-8

"""
Create jobfiles for `10-post_trials.py`.

##############################################################################
# Used seed range for post trial jobs: [300000, 400000]
##############################################################################
"""

import os
import numpy as np

from dagman import dagman
from _paths import PATHS
from _loader import time_window_loader


job_creator = dagman.DAGManJobCreator(mem=2)
job_name = "hese_transient_stacking"

job_dir = os.path.join(PATHS.jobs, "post_trials")
script = os.path.join(PATHS.repo, "10-post_trials.py")

# Get time windows
all_tw_ids = time_window_loader()
ntime_windows = len(all_tw_ids)

# 100 jobs a ~2h for 1e6 post trials
ntrials = int(1e6)
ntrials_per_job = int(1e4)
njobs_tot = int(ntrials / ntrials_per_job)
if ntrials != ntrials_per_job * njobs_tot:
    raise ValueError("Job settings does not lead to exactly " +
                     "{} trials".format(int(ntrials)))
print("Preparing {} total post trials".format(ntrials))
print("  - {} trials per job".format(ntrials_per_job))
print("Creating {} total jobfiles for all time windows".format(int(njobs_tot)))

# Make unique job identifiers:
# job_ids: 000 ... 999, 000 ... 999, ...
lead_zeros = int(np.ceil(np.log10(njobs_tot)))
job_ids = np.array(["{1:0{0:d}d}".format(lead_zeros, i)
                   for i in range(njobs_tot)])
job_args = {
    "rnd_seed": np.arange(300000, 300000 + njobs_tot).astype(int),
    "ntrials": njobs_tot * [ntrials_per_job],
    "job_id": job_ids,
    }

job_creator.create_job(script=script, job_args=job_args,
                       job_name=job_name, job_dir=job_dir, overwrite=True)
