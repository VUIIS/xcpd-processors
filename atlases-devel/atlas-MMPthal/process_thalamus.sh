#!/usr/bin/env bash

# Start with FSL Thalamus-maxprob atlas (1mm)
fslmaths /usr/local/fsl/data/atlases/Thalamus/Thalamus-maxprob-thr25-1mm.nii.gz -bin thalmask

# Resample to match MMP atlas (1.5mm)
#flirt \
#    -in thalmask \
#    -ref space-MNI152NLin2009cAsym_atlas-MMP_dseg \
#    -usesqform \
#    -applyxfm \
#    -interp nearestneighbour \
#    -out rthalmask

# We have 8464 voxels in the maxprob25 thalamus mask
#fslstats -K rthalmask rthalmask -m -v

#./make_thalamus_voxels.py

#fslmaths \
#    space-MNI152NLin2009cAsym_atlas-MMP_dseg \
#    -add rthalatlas \
#    space-MNI152NLin2009cAsym_atlas-MMPthal_dseg


## Alternative approach to match templateflow 2mm atlas tpl-MNI152NLin2009cAsym_res-02_T1w.nii.gz
## and thereby match an available fmriprep output
flirt \
    -in thalmask \
    -ref tpl-MNI152NLin2009cAsym_res-02_T1w.nii.gz \
    -usesqform \
    -applyxfm \
    -interp nearestneighbour \
    -out rthalmask

fslstats -K rthalmask rthalmask -m -v

./make_MMP_tsv.py
./make_thalamus_voxels.py

flirt \
    -in space-MNI152NLin2009cAsym_atlas-MMP_dseg \
    -ref tpl-MNI152NLin2009cAsym_res-02_T1w.nii.gz \
    -usesqform \
    -applyxfm \
    -interp nearestneighbour \
    -out space-MNI152NLin2009cAsym_res-02_atlas-MMP_dseg

fslmaths \
    space-MNI152NLin2009cAsym_res-02_atlas-MMP_dseg \
    -add rthalatlas \
    space-MNI152NLin2009cAsym_res-02_atlas-MMPthal_dseg

