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

from myi3scripts.hese import make_healpy_map_from_HESE_scan

inpath = os.path.join("/data", "ana", "Diffuse", "HESE", "Pass2_reconstruction",
                      "reconstruction_tracks", "Run*")
folders = glob(inpath)

outpath = os.path.join("/home", "user", "tmenne", "analysis", "hese_scan_maps")
outfiles = map(lambda p, name: os.path.join(p, name),
               zip(outpath, map(os.path.basename, folders)))

icemodel = "SpiceMie"
scan_str = "{}_nside????.i3.bz2".format(icemodel)


for i, folder in enumerate(folders):
    print("Working on scan:\n  {}".format(folder))
    print("Output file path:\n  {}".format(outfiles[i]))

    # make_healpy_map_from_HESE_scan(infolder=folder,
    #                                scan_file_str=scan_str,
    #                                outfile=outfiles[i],
    #                                coord="equ",
    #                                outfmt="json",
    #                                smooth_sigma=1.
    #                                )

print("Done!")
