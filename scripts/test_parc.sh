#!/usr/bin/env bash

./custom_parcellation.py \
    --fmriprep_dir /wkdir/INPUTS/fmriprep/fmriprepBIDS \
    --xcpd_dir /wkdir/INPUTS/xcpd/xcpdBIDS \
    --atlas CC20240607 \
    --min_coverage 0.5
