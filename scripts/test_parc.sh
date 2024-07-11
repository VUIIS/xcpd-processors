#!/usr/bin/env bash

./custom_parcellation.py \
    --fmriprep_dir ../INPUTS/fmriprep/fmriprepBIDS \
    --xcpd_dir ../INPUTS/xcpd/xcpdBIDS \
    --atlas_dir ../atlases \
    --atlas CC20240607 \
    --min_coverage 0.5 \
    --out_dir ../OUTPUTS
