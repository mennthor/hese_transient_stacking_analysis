# coding: utf-8

"""
Generate setting files to build the analysis objects with, including:

1) Settings for the tdepps injectors
2) Settings for the tdepps LLH models

By storing and reading the settings we can change them easily for tests without
messing up stuff in each analysis script.
"""

import os
import json
import numpy as np

from myi3scripts import serialize_ndarrays


PATH = os.path.join("/home", "tmenne", "analysis",
                    "hese_transient_stacking_analysis")

# Load time windows
fname = os.path.join(PATH, "out", "time_window_list", "time_windows.txt")
dt0, dt1 = np.loadtxt(fname, unpack=True, comments="#")

# :: Binning :: Used for injector and LLH models alike
# Finer resolution around the horizon region, where we usually switch the event
# selections from northern to southern samples
hor = np.sin(np.deg2rad(30))
sindec_bins = np.unique(np.concatenate([
                        np.linspace(-1., -hor, 3 + 1),    # south
                        np.linspace(-hor, +hor, 14 + 1),  # horizon
                        np.linspace(+hor, 1., 3 + 1),     # north
                        ]))

# :: BG Injector :: Settings for tdepps TimeDecDependentBGInjector




outpath = os.path.join("/home", "tmenne", "analysis",
                       "hese_transient_stacking_analysis", "out")
if not os.path.isdir(outpath):
    os.makedirs(outpath)
with open(os.path.join(outpath, "ana_settings.json"), "w") as f:
    json.dump(obj=llh_settings, fp=f, indent=2)

print("Saved LLH settings to:\n{}".format(outpath))

