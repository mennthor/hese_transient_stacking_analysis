# HESE Transient Stacking Analysis

Analysis wiki: [Transient_HESE_Stacking](https://wiki.icecube.wisc.edu/index.php/Transient_HESE_Stacking)

- Analyser: Thorben Menne
- Mail: thorben.menne@tu-dortmund.de
- Slack: @thorben

## Folder management

Working paths are set automatically by `_paths.py` to:

- `./<branch_name>_out/` for results
- `./<branch_name>_jobfiles/` for jobfiles
- `/data/user/tmenne/hese_transient_stacking_analysis/<branch_name>_rawout` for larger or intermediate cluster results.

## Redo the analysis

1. Clone or copy this this repository.
2. Install additional python software dependencies with `pip install --user -r py2requirements.txt` , which grabs some packages from pypi and custom packages from `/home/tmenne/software/`.
3. Executing each script here in order should rebuild all the files up to the final results.

### Note
For scripts, that need to run on the cluster, run the `_jobs.py` first, to create the jobfiles.
Then submit them using the `./jobfiles/<jobname>/*dag.start.sh` script on the submitter.
After all jobs are done run the `*_combine.py` script to collect the results.