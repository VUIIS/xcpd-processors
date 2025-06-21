#!/usr/bin/env bash

# atlas-MMPthal_space-MNI152NLin6Asym_res-02_dseg.nii.gz
#    1-360 cortex
#    10000-13537  thalamus voxels
#
# Delete thalamus voxels from MMPthal
fslmaths atlas-MMPthal_space-MNI152NLin6Asym_res-02_dseg.nii.gz \
    -uthr 361 cort_space-MNI152NLin6Asym_res-02_dseg.nii.gz
head -n 361 atlas-MMPthal_dseg.tsv > cort_dseg.tsv


# Atlas-Thalamus_space-MNI_hemi-left_label-AllNuclei_desc-MaxProb.nii
# Atlas-Thalamus_space-MNI_hemi-right_label-AllNuclei_desc-MaxProb.nii
fslmaths Atlas-Thalamus_space-MNI_hemi-left_label-AllNuclei_desc-MaxProb.nii.gz \
    -uthr 15 tmpL
fslmaths tmpL -add 400 -thr 401 thalL

fslmaths Atlas-Thalamus_space-MNI_hemi-right_label-AllNuclei_desc-MaxProb.nii.gz \
    -uthr 15 tmpR
fslmaths tmpR -add 500 -thr 501 thalR

fslmaths thalL -add thalR thal_hi

# Fix thal labels 402 left AV, 502 right AV etc

# Resample thal to 2mm geom



#  region	label
# 2	AV
# 4	VA
# 5	VLa
# 6	VLp
# 7	VPL
# 8 	PUL
# 9	LGN
# 10	MGN
# 11	CM
# 12	MD
# 13	Hb    DROP
# 14	MTT   DROP
# 17	CL    DROP
# 18	VPM   DROP

