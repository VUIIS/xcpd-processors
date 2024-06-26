#!/usr/bin/env bash

funcdir=../INPUTS/fmriprep/fmriprepBIDS/sub-Caltech51456/ses-Caltech51456/func
xcpdir=../INPUTS/xcpd/xcpdBIDS/sub-Caltech51456/ses-Caltech51456/func
roidir=../rois

./custom_parcellation.py \
    --mask_niigz ${funcdir}/sub-Caltech51456_ses-Caltech51456_task-rest_run-1_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz \
    --temporalmask_tsv "" \
    --fmri_niigz ${xcpdir}/sub-Caltech51456_ses-Caltech51456_task-rest_run-1_space-MNI152NLin2009cAsym_desc-denoised_bold.nii.gz \
    --atlas_niigz ${roidir}/tpl-MNI152NLin6Asym_atlas-CC20240607_dseg.nii.gz \
    --atlaslabels_tsv ${roidir}/atlas-CC20240607_dseg.tsv \
    --min_coverage 0.5
