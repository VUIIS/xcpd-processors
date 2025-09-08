#!/usr/bin/env bash

# Overall indexing
#      1-360  MMP cortex
#    402-423  rh THOMAS thal
#    502-523  lh THOMAS thal
#    601-650  Tian subcortical excluding thalamus

# atlas-MMPthal_space-MNI152NLin6Asym_res-02_dseg.nii.gz
#    1-360 cortex
#    10000-13537  thalamus voxels (will be removed)
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
fslmaths tmpL -add 500 -thr 501 thalL

fslmaths Atlas-Thalamus_space-MNI_hemi-right_label-AllNuclei_desc-MaxProb.nii.gz \
    -uthr 12 tmpR
fslmaths tmpR -add 400 -thr 401 thalR

fslmaths thalL -add thalR thal_hi

rm tmpL.nii.gz tmpR.nii.gz

# Resample thal to 2mm geom
flirt -in thal_hi \
	-ref cort_space-MNI152NLin6Asym_res-02_dseg \
	-out thal_lo \
	-usesqform \
	-applyxfm \
	-interp nearestneighbour

# Create mask to avoid overlaps with Tian
fslmaths cort_space-MNI152NLin6Asym_res-02_dseg -add thal_lo -bin cortthalmask

# Tian level 3 excluding thalamus
# Remove any unaccounted-for Tian thalamus voxels (5-10,21,30-35,46) then just add 600
tsc=Tian2020MSA/3T/Subcortex-Only/Tian_Subcortex_S3_3T
fslmaths $tsc -thr 5 -uthr 10 -bin -add cortthalmask -bin cortthalmask
fslmaths $tsc -thr 21 -uthr 21 -bin -add cortthalmask -bin cortthalmask
fslmaths $tsc -thr 30 -uthr 35 -bin -add cortthalmask -bin cortthalmask
fslmaths $tsc -thr 46 -uthr 46 -bin -add cortthalmask -bin cortthalmask
fslmaths cortthalmask -sub 1 -mul -1 antimask
fslmaths $tsc -bin tianmask
fslmaths $tsc -add 600 -mul antimask -mul tianmask reduced_tian

# Combine
fslmaths cort_space-MNI152NLin6Asym_res-02_dseg \
	-add thal_lo \
	-add reduced_tian \
	atlas-MMPthalTian_space-MNI152NLin6Asym_res-02_dseg


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
402	rh_thal_AV
404	rh_thal_VA
405	rh_thal_VLa
406	rh_thal_VLp
407	rh_thal_VPL
408	rh_thal_PUL
409	rh_thal_LGN
410	rh_thal_MGN
411	rh_thal_CM
412	rh_thal_MD
502	lh_thal_AV
504	lh_thal_VA
505	lh_thal_VLa
506	lh_thal_VLp
507	lh_thal_VPL
508	lh_thal_PUL
509	lh_thal_LGN
510	lh_thal_MGN
511	lh_thal_CM
512	lh_thal_MD
EOF

# Make the complete label list
cat cort_dseg.tsv thal_dseg.tsv reducedtian_dseg.tsv > atlas-MMPthalTian_dseg.tsv
