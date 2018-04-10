# HESE Transient Stacking Analysis

Analysis wiki: [Transient_HESE_Stacking](https://wiki.icecube.wisc.edu/index.php/Transient_HESE_Stacking)

- Analyser: Thorben Menne
- Mail: thorben.menne@tu-dortmund.de
- Slack: @thorben

## Redo the analysis

Working paths are `./out/` for results and `/data/user/tmenne/hese_transient_stacking_analysis/` for larger or intermediate cluster results.

1. Clone or copy this this repository.
2. Install additional python software dependencies with `pip install --user -e .` from within their repositories (find them in `/home/tmenne/software/`):
    - dagman
        + Tool to create dagman jobfiles
    - myi3scripts
        + Collection of helper functions
    - tdepps
        + Main analysis module
        + Note: Needs `devset2` to compile the C++ backend (April 2018)
3. Executing each script here in order should rebuild all the files up to the final results.

### Note
For scripts, that need to run on the cluster, run the `_jobs.py` first, to create the jobfiles.
Then submit them using the `./jobfiles/<jobname>/*dag.start.sh` script on the submitter.
After all jobs are done run the `*_combine.py` script to collect the results.