# coding: utf-8

"""
Make a post trial -log01(p) PDF object stored as JSON.
"""

import os
import json
import gzip
import numpy as np

from tdepps.utils.stats import PureEmpiricalDist

from _paths import PATHS, check_dir
from _loader import bg_pdf_loader


outpath = os.path.join(PATHS.local, "post_trials_pdf")
check_dir(outpath, ask=True)

# Load post trials
fname = os.path.join(PATHS.local, "post_trials_combined", "post_trials.json.gz")
with gzip.open(fname) as infile:
    post_trials = json.load(infile)
    ts = np.array(post_trials["ts"])
    print("Loaded post trials from:\n  {}".format(fname))

# Load BG pdfs, get the smallest p-value per trial and make a -lo10(p) PDF
bg_pdfs = bg_pdf_loader("all")
pvals = np.ones_like(ts)
for i, bg_pdf in bg_pdfs.items():
    pvals[:, i] = bg_pdf.sf(ts[:, i])

# Create an empirical PDF object for the post trial PDF
neg_log10_post_pvals = -np.log10(np.amin(pvals, axis=1))
post_neglog10_pdf = PureEmpiricalDist(neg_log10_post_pvals)

outfile = os.path.join(outpath, "neg_log10_post_pdf.json.gz")
with gzip.open(outfile, "w") as fp:
    fp.write(post_neglog10_pdf.to_json(dtype=float))
    print("Saved PDF as JSON to:\n  {}".format(outfile))
