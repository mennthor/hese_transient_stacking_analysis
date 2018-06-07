# coding: utf-8

"""
Single job of performance trials.
Loads data and settings and builds the models, likelihoods and injectors to do
the trials with.
Signal is injected with multiple means to robustly estimate the performance by
fitting a generic but matching chi2 distribution to the trial results.
"""

import gc
import os
import json
import gzip
import argparse
import numpy as np

from tdepps.utils import make_src_records
from tdepps.grb import GRBLLH, GRBModel, MultiGRBLLH
from tdepps.grb import TimeDecDependentBGDataInjector
from tdepps.grb import UniformTimeSampler, SignalFluenceInjector
from tdepps.grb import HealpySignalFluenceInjector
from tdepps.grb import MultiBGDataInjector, MultiSignalFluenceInjector
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
parser.add_argument("--tw_id", type=int)
parser.add_argument("--sig_inj", type=str)
args = parser.parse_args()
rnd_seed = args.rnd_seed
ntrials = args.ntrials
tw_id = args.tw_id
sig_inj_type = args.sig_inj

rndgen = np.random.RandomState(rnd_seed)
dt0, dt1 = _loader.time_window_loader(tw_id)
time_sam = UniformTimeSampler(random_state=rndgen)

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

    # Setup Signal injector
    fmod = opts["sig_inj_opts"].pop("flux_model")
    flux_model = flux_model_factory(fmod["model"], **fmod["args"])
    # Decide what type of injection we need
    if sig_inj_type == "healpy":
        # Inject source position from prior map, worsening performance
        opts["sig_inj_opts"]["inj_sigma"] = 3.
        src_maps = _loader.source_map_loader(src_list=srcs)
        sig_inj_i = HealpySignalFluenceInjector(
            flux_model, time_sampler=time_sam, inj_opts=opts["sig_inj_opts"],
            random_state=rndgen)
        sig_inj_i.fit(srcs_rec, src_maps=src_maps, MC=mc)
        del src_maps
    elif sig_inj_type == "ps":
        # Always inject the best fit source position, exactly as tested
        sig_inj_i = SignalFluenceInjector(
            flux_model, time_sampler=time_sam, inj_opts=opts["sig_inj_opts"],
            random_state=rndgen)
        sig_inj_i.fit(srcs_rec, MC=mc)
    else:
        raise ValueError("`sig_inj_type` can be 'ps' or 'healpy'.")
    sig_injs[key] = sig_inj_i

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

multi_sig_inj = MultiSignalFluenceInjector(random_state=rndgen)
multi_sig_inj.fit(sig_injs)

multi_llh_opts = _loader.settings_loader("multi_llh")["multi_llh"]
multi_llh = MultiGRBLLH(llh_opts=multi_llh_opts)
multi_llh.fit(llhs=llhs)

ana = GRBLLHAnalysis(multi_llh, multi_bg_inj, sig_inj=multi_sig_inj)

# Do the performance trials
print("Time window ID is: {}".format(tw_id))
print(":: Starting performance trials ::")
# These can be changed later with the generated trials, just set them to
# 90% over ts=0 to init it with something
beta = 0.9
ts_val = 0.
# Seed close to zero, which is close to the minimum for most cases
ns0 = .1

# Scan dense and large enough region for discovery potentials
if sig_inj_type == "ps":
    mu_sig = np.r_[0.1, np.arange(0.5, 15.5, 0.5)]
elif sig_inj_type == "healpy":
    mu_sig = np.r_[0.1, 0.5, np.arange(1., 30., 1.)]
    if tw_id > 16:
        mu_sig = np.r_[0.1, 0.5, np.arange(1., 60., 2.)]

perf = ana.performance(ts_val=ts_val, beta=beta, mus=mu_sig, ns0=ns0,
                       n_batch_trials=ntrials)
print(":: Done ::")

# Convert ndarrays and lists of ndarrays to lists of lists for JSON
out = {
    "beta": perf["beta"],
    "ninj": [arr.tolist() for arr in perf["ninj"]],
    "cdfs": perf["cdfs"].tolist(),
    "mus": perf["mus"].tolist(),
    "mu_bf": perf["mu_bf"],
    "tsval": perf["tsval"],
    "pars": perf["pars"].tolist(),
    "ns": [arr.tolist() for arr in perf["ns"]],
    "ts": [arr.tolist() for arr in perf["ts"]],
    }

# Save as JSON
outpath = os.path.join(PATHS.data, "performance_trials_" + sig_inj_type)
if not os.path.isdir(outpath):
    os.makedirs(outpath)

fname = os.path.join(outpath, "tw_{:02d}.json.gz".format(tw_id))
with gzip.open(fname, "w") as outfile:
    json.dump(out, fp=outfile, indent=1)
    print("Saved to:\n  {}".format(fname))
