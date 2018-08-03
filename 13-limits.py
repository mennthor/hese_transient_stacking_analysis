# coding: utf-8

"""
Single job of scanning limits around the best fit in spectral index and time
window.
"""

import gc
import os
import json
import gzip
import argparse
import numpy as np

from tdepps.utils import make_src_records, flux_model_factory
from tdepps.grb import GRBLLH, GRBModel, MultiGRBLLH
from tdepps.grb import TimeDecDependentBGDataInjector
from tdepps.grb import UniformTimeSampler, HealpySignalFluenceInjector
from tdepps.grb import MultiBGDataInjector, MultiSignalFluenceInjector
from tdepps.grb import GRBLLHAnalysis
from _paths import PATHS
import _loader


parser = argparse.ArgumentParser(description="hese_stacking")
parser.add_argument("--rnd_seed", type=int)
parser.add_argument("--ntrials", type=int)
parser.add_argument("--tw_id", type=int)
parser.add_argument("--gamma", type=float)
args = parser.parse_args()
rnd_seed = args.rnd_seed
ntrials = args.ntrials
tw_id = args.tw_id
gamma = args.gamma

if gamma < 0.:
    raise ValueError("`gamma` is a positive spectral index, use it > 0.")

rndgen = np.random.RandomState(rnd_seed)
time_sam = UniformTimeSampler(random_state=rndgen)

# Load result against which the limits are calculated
res = _loader.result_loader()
best_tw_idx = res["best_idx"]
best_ts_val = res["ts"][best_tw_idx]
best_dt0, best_dt1 = _loader.time_window_loader(best_tw_idx)
beta = 0.9  # 90% upper limit

# Signal injection time window
dt0, dt1 = _loader.time_window_loader(tw_id)

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
    # Change time window for injection sources, always test against the best fit
    test_srcs_rec = make_src_records(srcs, dt0=best_dt0, dt1=best_dt1)
    sig_inj_srcs_rec = make_src_records(srcs, dt0=dt0, dt1=dt1)

    # Setup BG injector
    bg_inj_i = TimeDecDependentBGDataInjector(inj_opts=opts["bg_inj_opts"],
                                              random_state=rndgen)
    bg_inj_i.fit(X=exp_off, srcs=test_srcs_rec, run_list=runlist)
    bg_injs[key] = bg_inj_i

    # Setup signal injector with current gamma (and only the signal injector)
    fmod = opts["sig_inj_opts"].pop("flux_model")
    fmod["args"]["gamma"] = gamma
    flux_model = flux_model_factory(fmod["model"], **fmod["args"])

    # Inject source position from prior map, worsening performance
    opts["sig_inj_opts"]["inj_sigma"] = 3.
    src_maps = _loader.source_map_loader(src_list=srcs)
    sig_inj_i = HealpySignalFluenceInjector(
        flux_model, time_sampler=time_sam, inj_opts=opts["sig_inj_opts"],
        random_state=rndgen)
    sig_inj_i.fit(sig_inj_srcs_rec, src_maps=src_maps, MC=mc)
    sig_injs[key] = sig_inj_i
    del src_maps

    # Setup LLH model and LLH
    fmod = opts["model_energy_opts"].pop("flux_model")
    flux_model = flux_model_factory(fmod["model"], **fmod["args"])
    opts["model_energy_opts"]["flux_model"] = flux_model
    llhmod = GRBModel(spatial_opts=opts["model_spatial_opts"],
                      energy_opts=opts["model_energy_opts"])
    llhmod.fit(X=exp_off, MC=mc, srcs=test_srcs_rec, run_list=runlist)
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

ana = GRBLLHAnalysis(multi_llh, multi_bg_inj, sig_inj=multi_sig_inj,
                     random_state=rndgen)

# Do the performance trials
print("Signal inject with time window ID  : {}".format(tw_id))
print("Signal injected with spectral index: {}".format(gamma))
print("Tested with time window            : {}".format(best_tw_idx))
print(":: Starting performance trials ::")
# Seed close to zero, which is close to the minimum for most cases
ns0 = 0.1

# Scan dense and large enough regions for discovery potentials
if tw_id < 10:
    mu_sig = np.r_[0.1, 0.5, np.arange(1., 30., 1.)]
elif (tw_id >= 10) and (tw_id < 16):
    mu_sig = np.r_[0.1, 0.5, np.arange(1., 60., 2.)]
if tw_id >= 16:
    mu_sig = np.r_[0.1, 0.5, np.arange(1., 90., 3.)]

perf = ana.performance(ts_val=best_ts_val, beta=beta, mus=mu_sig, ns0=ns0,
                       n_batch_trials=ntrials)
print(":: Done ::")

# Convert ndarrays and lists of ndarrays to lists of lists for JSON
out = {
    "beta": perf["beta"],
    "ninj": [arr.tolist() for arr in perf["ninj"]],
    "cdfs": perf["cdfs"].tolist(),
    "mus": perf["mus"].tolist(),
    "mu_bf": perf["mu_bf"],
    "flux_bf": multi_sig_inj.mu2flux(perf["mu_bf"]),
    "tsval": perf["tsval"],
    "pars": perf["pars"].tolist(),
    "ns": [arr.tolist() for arr in perf["ns"]],
    "ts": [arr.tolist() for arr in perf["ts"]],
    "gamma": gamma,
    }

# Save as JSON
outpath = os.path.join(PATHS.data, "limits_healpy")
if not os.path.isdir(outpath):
    os.makedirs(outpath)

fname = os.path.join(outpath, "tw_{:02d}_gamma_{:.1f}.json.gz".format(
    tw_id, gamma))
with gzip.open(fname, "w") as outfile:
    json.dump(out, fp=outfile, indent=1)
    print("Saved to:\n  {}".format(fname))
