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

from myi3scripts.hese import make_healpy_map_from_HESE_scan


print("Start: {}\n".format(datetime.datetime.utcnow()))

inpath = os.path.join("/data", "ana", "Diffuse", "HESE", "Pass2_reconstruction",
                      "reconstruction_tracks", "Run*")
folders = glob(inpath)

outpath = os.path.join("/home", "user", "tmenne", "analysis", "hese_scan_maps")
outfiles = map(lambda name: os.path.join(outpath, name),
               map(os.path.basename, folders))

icemodel = "SpiceMie"
scan_str = "{}_nside????.i3.bz2".format(icemodel)


for infolder, outfile in zip(folders, outfiles):
    print("Working on scan:\n  {}".format(infolder))
    print("Output file path:\n  {}".format(outfile))

    # make_healpy_map_from_HESE_scan(infolder=infolder,
    #                                scan_file_str=scan_str,
    #                                outfile=outfile,
    #                                coord="equ",
    #                                outfmt="json",
    #                                smooth_sigma=1.,
    #                                )

print("\nDone: {}".format(datetime.datetime.utcnow()))
