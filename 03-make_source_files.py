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


PATHS = json.load(open("./WORK_DIRS.json"))

src_path = os.path.join(PATHS["local"], "hese_scan_maps")
runlist_path = os.path.join(PATHS["local"], "runlists")

# TODO: Load runlists and sources
