#!/usr/bin/env bash

# Start with FSL Thalamus-maxprob atlas (1mm)
fslmaths /usr/local/fsl/data/atlases/Thalamus/Thalamus-maxprob-thr25-1mm.nii.gz -bin thalmask

# Resample to match MMP atlas (1.5mm)
flirt \
    -in thalmask \
    -ref space-MNI152NLin2009cAsym_atlas-MMP_dseg \
    -usesqform \
    -applyxfm \
    -interp nearestneighbour \
    -out rthalmask

# We have 8464 voxels in the maxprob25 thalamus mask
fslstats -K rthalmask rthalmask -m -v
