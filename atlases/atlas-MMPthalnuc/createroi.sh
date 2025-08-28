#!/usr/bin/env bash

# atlas-MMPthal_space-MNI152NLin6Asym_res-02_dseg.nii.gz
#    1-360 cortex
#    10000-13537  thalamus voxels
#
# Delete thalamus voxels from MMPthal cortical atlas that we already have
fslmaths atlas-MMPthal_space-MNI152NLin6Asym_res-02_dseg.nii.gz \
    -uthr 361 cort_space-MNI152NLin6Asym_res-02_dseg.nii.gz
head -n 361 atlas-MMPthal_dseg.tsv > cort_dseg.tsv

# Combine thalamus hi-res atlas
# Atlas-Thalamus_space-MNI_hemi-left_label-AllNuclei_desc-MaxProb.nii
# Atlas-Thalamus_space-MNI_hemi-right_label-AllNuclei_desc-MaxProb.nii
fslmaths Atlas-Thalamus_space-MNI_hemi-left_label-AllNuclei_desc-MaxProb.nii.gz \
    -uthr 12 tmpL
fslmaths tmpL -add 400 -thr 401 thalL

fslmaths Atlas-Thalamus_space-MNI_hemi-right_label-AllNuclei_desc-MaxProb.nii.gz \
    -uthr 12 tmpR
fslmaths tmpR -add 500 -thr 501 thalR

fslmaths thalL -add thalR thal_hi

# Resample thal to 2mm geom
flirt -in thal_hi \
	-ref cort_space-MNI152NLin6Asym_res-02_dseg \
	-out thal_lo \
	-usesqform \
	-applyxfm \
	-interp nearestneighbour

# Combine
fslmaths cort_space-MNI152NLin6Asym_res-02_dseg -add thal_lo \
	atlas-MMPthalnuc_space-MNI152NLin6Asym_res-02_dseg

# Thal labels +400 for left, +500 for right
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
cat << EOF > thal_dseg.tsv
402	lh_thal_AV
404	lh_thal_VA
405	lh_thal_VLa
406	lh_thal_VLp
407	lh_thal_VPL
408	lh_thal_PUL
409	lh_thal_LGN
410	lh_thal_MGN
411	lh_thal_CM
412	lh_thal_MD
502	rh_thal_AV
504	rh_thal_VA
505	rh_thal_VLa
506	rh_thal_VLp
507	rh_thal_VPL
508	rh_thal_PUL
509	rh_thal_LGN
510	rh_thal_MGN
511	rh_thal_CM
512	rh_thal_MD
EOF

# Make the complete label list
cat cort_dseg.tsv thal_dseg.tsv > atlas-MMPthalnuc_dseg.tsv
