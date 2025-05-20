# Configuring XCP_D processors for DAX/XNAT

## Resource requirements

    requirements:
      walltime: 1-0
      memory: 8000

One CPU for one day with 8 GB of memory probably suffices. These might need to be increased
for high resolution data (< 2.5mm fmri voxel size) or large number of connectivity map
outputs.


## Inputs

    inputs:
      xnat:  
        scans:
          - name: scan_fmri
            types: REST
        assessors:
          - name: assr_fmriprep
            proctypes: fmriprep-ABIDE_v23

Verify that all fmri scan types are listed, and the appropriate fmriprep proctype is
set.


## XCP_D command line flags in main command

Verify that the XCP_D options suit the needs of the project. Reference is here: https://xcp-d.readthedocs.io/en/latest/usage.html

Some commonly changed options are

    --atlases Glasser
    --nuisance-regressors acompcor
    --fd-thresh 0
    --lower-bpf 0.01
    --upper-bpf 0.10
    --min-coverage 0.5


## Post processing: Standard

`stats_csvs.py` reformats QC stats to CSV format suitable for REDCap sync.

`fisher_z.py` computes Fisher Z score matrices from the Pearson correlation matrices.


## Post processing: Non-standard atlas

`custom_parcellation.py` is used if the desired atlas is not one of the XCP_D standards.
Check the correct `--space` is set (must be present in fmriprep, typically `MNI152NLin6Asym`
or `MNI152NLin2009cAsym`). The atlas must be present and correctly configured in this repo.

    custom_parcellation.py
      --fmriprep_dir /INPUTS/fmriprepBIDS/fmriprepBIDS
      --xcpd_dir /OUTPUTS/xcpdBIDS
      --space MNI152NLin6Asym
      --atlas BNST
      --min_coverage 0.5
      --out_dir /OUTPUTS


## Post processing: Connectivity maps

`connectivity_maps.py` is used to generate connectivity maps. Do not generate maps that are
not genuinely needed - these use considerable disk space.

    connectivity_maps.py
      --xcpd_dir /OUTPUTS/xcpdBIDS
      --space MNI152NLin6Asym
      --atlas BNST
      --saveR
      --saveZ
      --fwhm 0 4

Options are

    --saveR         creates Pearson correlation maps
    --saveA         creates Fisher Z maps
    --fwhm          list of smoothing kernels to apply to maps
    --seeds         list of seed regions to create maps for (all, if not given)
