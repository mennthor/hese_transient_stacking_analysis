# coding: utf-8

"""
Single job of background only post-trials.
Loads data and settings and builds the models, likelihoods and injectors to do
the trials with.

First part build models and injectors exactly as in BG trials.
"""

import gc  # Manual garbage collection
import os
import json
import gzip
import argparse
import numpy as np
from copy import deepcopy

from tdepps.utils import make_src_records
from tdepps.grb import GRBLLH, GRBModel, MultiGRBLLH
from tdepps.grb import TimeDecDependentBGDataInjector
from tdepps.grb import MultiBGDataInjector
from tdepps.grb import GRBLLHAnalysis
import tdepps.utils.phys as phys
from _paths import PATHS
import _loader


def flux_model_factory(model, **model_args):
    """
    Returns a flux model callable `flux_model(trueE)`.

    Parameters
    ----------
    model : str
        Name of a method in ``tdeps.utils.phys``.
    model_args : dict
        Arguments passed to ``tdeps.utils.phys.<model>``.

    Returns
    -------
    flux_model : callable
        Function of single parameter, true energy, with fixed model args.
    """
    def flux_model(trueE):
        flux_mod = getattr(phys, model)
        return flux_mod(trueE, **model_args)

    return flux_model


parser = argparse.ArgumentParser(description="hese_stacking")
parser.add_argument("--rnd_seed", type=int)
parser.add_argument("--ntrials", type=int)
parser.add_argument("--job_id", type=str)
args = parser.parse_args()
rnd_seed = args.rnd_seed
ntrials = args.ntrials
job_id = args.job_id

rndgen = np.random.RandomState(rnd_seed)
# Load the largest time window for the injector
dt0, dt1 = _loader.time_window_loader(-1)

# Load files and build the models one after another to save memory
bg_injs = {}
sig_injs = {}
llhs = {}

# Load files and build the models one after another to save memory
sample_names = _loader.source_list_loader()
for key in sample_names:
    print("\n" + 80 * "#")
    print("# :: Setup for sample {} ::".format(key))
    opts = _loader.settings_loader(key)[key].copy()
    exp_off = _loader.off_data_loader(key)[key]
    mc = _loader.mc_loader(key)[key]
    srcs = _loader.source_list_loader(key)[key]
    runlist = _loader.runlist_loader(key)[key]
    # Process to tdepps format
    srcs_rec = make_src_records(srcs, dt0=dt0, dt1=dt1)

    # Setup BG injector
    bg_inj_i = TimeDecDependentBGDataInjector(inj_opts=opts["bg_inj_opts"],
                                              random_state=rndgen)
    bg_inj_i.fit(X=exp_off, srcs=srcs_rec, run_list=runlist)
    bg_injs[key] = bg_inj_i

    # Setup LLH model and LLH
    fmod = opts["model_energy_opts"].pop("flux_model")
    flux_model = flux_model_factory(fmod["model"], **fmod["args"])
    opts["model_energy_opts"]["flux_model"] = flux_model
    llhmod = GRBModel(X=exp_off, MC=mc, srcs=srcs_rec, run_list=runlist,
                      spatial_opts=opts["model_spatial_opts"],
                      energy_opts=opts["model_energy_opts"])
    llhs[key] = GRBLLH(llh_model=llhmod, llh_opts=opts["llh_opts"])

    del exp_off
    del mc
    gc.collect()

# Build the multi models
multi_bg_inj = MultiBGDataInjector()
multi_bg_inj.fit(bg_injs)

multi_llh_opts = _loader.settings_loader("multi_llh")["multi_llh"]
multi_llh = MultiGRBLLH(llh_opts=multi_llh_opts)
multi_llh.fit(llhs=llhs)

ana = GRBLLHAnalysis(multi_llh, multi_bg_inj, sig_inj=None)

# Do the post trials
# Prepare a list of LLHs each with a different time window to test.
dt0s, dt1s = _loader.time_window_loader("all")
test_llhs = []
for i, (dt0i, dt1i) in enumerate(zip(dt0s, dt1s)):
    print("# Build test LLH for time window pair {}".format(i))
    test_multi_llh = deepcopy(ana.llh)
    for key, model in test_multi_llh.model.items():
        print("- {}".format(key))
        model.set_new_srcs_dt(dt0=dt0i, dt1=dt1i, copy=False)

    test_llhs.append(test_multi_llh)

print(":: Starting {} background post trials ::".format(ntrials))
trials = ana.post_trials(n_trials=ntrials, test_llhs=test_llhs, ns0=0.1)
print(":: Done ::")

# Save as JSON
outpath = os.path.join(PATHS.data, "post_trials")
if not os.path.isdir(outpath):
    os.makedirs(outpath)

out = {"ns": [arr.tolist() for arr in trials["ns"]],
       "ts": [arr.tolist() for arr in trials["ts"]],
       "rnd_seed": rnd_seed,
       "ntrials": ntrials,
       "time_windows": [dt0s.tolist(), dt1s.tolist()]}  # Same order as LLHs

fname = os.path.join(outpath, "job_{}.json.gz".format(job_id))
with gzip.open(fname, "w") as outfile:
    json.dump(out, fp=outfile, indent=2)
    print("Saved to:\n  {}".format(fname))
