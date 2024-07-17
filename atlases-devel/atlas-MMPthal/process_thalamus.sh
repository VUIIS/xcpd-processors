#!/usr/bin/env bash

# Process atlas-MMP_space-MNI152NLin2009cAsym_res-015 to match fmriprep MNI152NLin6Asym space,
# and add thalamus voxel ROIs
#
# See get_templateflow.py to get specific atlas image for grid reference

# Get thalamus mask from FSL maxprob and resample to template grid
fslmaths /usr/local/fsl/data/atlases/Thalamus/Thalamus-maxprob-thr25-1mm.nii.gz -bin thalmask
flirt \
    -in thalmask \
    -ref tpl-MNI152NLin6Asym_res-02_T1w \
    -usesqform \
    -applyxfm \
    -interp nearestneighbour \
    -out rthalmask

# Make tsv labels for the MMP atlas
./make_MMP_tsv.py

# Make thalamus voxel ROIs and add their labels to the list
./make_thalamus_voxels.py

# Resample the source MMP atlas to desired grid
flirt \
    -in atlas-MMP_space-MNI152NLin2009cAsym_res-015 \
    -ref tpl-MNI152NLin6Asym_res-02_T1w \
    -usesqform \
    -applyxfm \
    -interp nearestneighbour \
    -out atlas-MMP_space-MNI152NLin6Asym_res-02_dseg

# Add the thalamus ROIs
fslmaths \
    atlas-MMP_space-MNI152NLin6Asym_res-02_dseg \
    -add rthalatlas \
    atlas-MMPthal_space-MNI152NLin6Asym_res-02_dseg





