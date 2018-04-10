# coding: utf-8

"""
Use runlists to build a JSON file with the needed source information and to
which sample each on belongs to.
"""

import os
import json
import gzip
import numpy as np
import astropy.time as astrotime

from skylab.datasets import Datasets


inpath = os.path.join("/home", "tmenne", "analysis",
                      "hese_transient_stacking_analysis", "out")

src_path = os.path.join(inpath, "hese_scan_maps")
runlist_path = os.path.join(inpath, "runlists")

# TODO: Load runlists and sources
