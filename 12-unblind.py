# coding: utf-8

"""
Unblind held back ontime data.
"""

from __future__ import print_function
import gc
import os
from copy import deepcopy
import json
import argparse
import numpy as np

from tdepps.utils import make_src_records, prob2sigma
from tdepps.grb import TimeDecDependentBGDataInjector, MultiBGDataInjector
from tdepps.grb import GRBLLH, GRBModel, MultiGRBLLH
from tdepps.grb import GRBLLHAnalysis
import tdepps.utils.phys as phys
from _paths import PATHS, check_dir
import _loader


def dict_print(d):
    shift = max(map(len, d.keys())) + 1
    for key, val in d.items():
        print("{0:{1:d}s}: ".format(key, shift), val)


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
parser.add_argument("--rnd_seed", type=int, default=None)
parser.add_argument("--really_unblind", action="store_true")
args = parser.parse_args()
rnd_seed = args.rnd_seed
really_unblind = args.really_unblind

bg_injs = {}
llhs = {}
rndgen = np.random.RandomState(rnd_seed)
dt0, dt1 = _loader.time_window_loader(-1)
sample_names = _loader.source_list_loader()

# Load files and build the models one after another to save memory
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
    llhmod = GRBModel(spatial_opts=opts["model_spatial_opts"],
                      energy_opts=opts["model_energy_opts"])
    llhmod.fit(X=exp_off, MC=mc, srcs=srcs_rec, run_list=runlist)
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

# Load the BG trial and post-trial PDFs
post_trial_pdf = _loader.post_trial_pdf_loader()
bg_pdfs = _loader.bg_pdf_loader("all")

# Prepare a list of LLHs each with a different time window to test.
dt0s, dt1s = _loader.time_window_loader("all")
test_llhs = {}
for i, (dt0i, dt1i) in enumerate(zip(dt0s, dt1s)):
    print("# Build test LLH for time window pair {}: [{:.0f}, {:.0f}]".format(
        i, dt0i, dt1i))
    test_multi_llh = deepcopy(ana.llh)
    for key, model in test_multi_llh.model.items():
        print("- {}".format(key))
        # Switch time windows and register new model
        new_model = model.set_new_srcs_dt(dt0=dt0i, dt1=dt1i)
        test_multi_llh.llhs[key].model = new_model

    test_llhs[i] = test_multi_llh

# ##############################################################################
# Get the unblinded result
exp_on = _loader.on_data_loader("all")
result = ana.unblind(X=exp_on, test_llhs=test_llhs, bg_pdfs=bg_pdfs, ns0=0.1,
                     post_trial_pdf=post_trial_pdf,
                     really_unblind=really_unblind)
result["sigma"] = prob2sigma(1. - result["post_pval"])[0]
# ##############################################################################

# Save as JSON
outpath = os.path.join(PATHS.local, "unblinding")
check_dir(outpath, ask=False)

fname = os.path.join(outpath, "result.json")
with open(fname, "w") as fp:
    json.dump(result, fp=fp, indent=1)
    print("Saved to:\n  {}".format(fname))

# Print result
dict_print(result)
