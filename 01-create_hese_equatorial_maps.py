# coding: utf8

"""
Make complete healpy logLLH maps from HESE scans and save in npy or json as
simple arrays.

Find pass2 scan files at:
    /data/ana/Diffuse/HESE/Pass2_reconstruction/reconstruction_tracks
"""
from __future__ import print_function, division
import os
from glob import glob
import datetime

# pip install --user futures
from concurrent.futures import ProcessPoolExecutor, wait

from myi3scripts.hese import make_healpy_map_from_HESE_scan


print("Start: {}\n".format(datetime.datetime.utcnow()))

inpath = os.path.join("/data", "ana", "Diffuse", "HESE", "Pass2_reconstruction",
                      "reconstruction_tracks", "Run*")
folders = sorted(glob(inpath))

outpath = os.path.join("/home", "tmenne", "analysis",
                       "hese_transient_stacking_analysis", "out",
                       "hese_scan_maps")
if not os.path.isdir(outpath):
    os.makedirs(outpath)
outfiles = map(lambda name: os.path.join(outpath, name),
               map(os.path.basename, folders))

icemodel = "SpiceMie"
scan_str = "{}_nside????.i3.bz2".format(icemodel)

# Work on multiple maps at once. If module not available, loop over all files
N_JOBS = 20
with ProcessPoolExecutor(max_workers=N_JOBS) as executor:
    processes = []
    for infolder, outfile in zip(folders, outfiles):
        processes.append(
            executor.submit(
                make_healpy_map_from_HESE_scan,
                infolder=infolder,
                scan_file_str=scan_str,
                outfile=outfile,
                coord="equ",
                outfmt="json",
                smooth_sigma=1.,
                )
            )
    results = wait(processes)

print("\nDone: {}".format(datetime.datetime.utcnow()))
