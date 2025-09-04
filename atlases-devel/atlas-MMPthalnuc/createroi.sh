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

rm tmpL.nii.gz tmpR.nii.gz

# Resample thal to 2mm geom
flirt -in thal_hi \
	-ref cort_space-MNI152NLin6Asym_res-02_dseg \
	-out thal_lo \
	-usesqform \
	-applyxfm \
	-interp nearestneighbour

# Extract hippocampus from Tian level 3
# FIXME One of these has a tiny bit of overlap with 122 in cortex so mask out cortex
#
#  1  rh_HIP_head_m
#  2  rh_HIP_head_l
#  3  rh_HIP_body
#  4  rh_HIP_tail
# 26  lh_HIP_head_m
# 27  lh_HIP_head_l
# 28  lh_HIP_body
# 29  lh_HIP_tail
tsc=Tian2020MSA/3T/Subcortex-Only/Tian_Subcortex_S3_3T
fslmaths $tsc -thr 25.5 -uthr 26.5 -bin -mul 420 lh_HIP_head_m
fslmaths $tsc -thr 26.5 -uthr 27.5 -bin -mul 421 lh_HIP_head_l
fslmaths $tsc -thr 27.5 -uthr 28.5 -bin -mul 422 lh_HIP_body
fslmaths $tsc -thr 28.5 -uthr 29.5 -bin -mul 423 lh_HIP_tail
fslmaths $tsc -thr 0.5 -uthr 1.5 -bin -mul 520 rh_HIP_head_m
fslmaths $tsc -thr 1.5 -uthr 2.5 -bin -mul 521 rh_HIP_head_l
fslmaths $tsc -thr 2.5 -uthr 3.5 -bin -mul 522 rh_HIP_body
fslmaths $tsc -thr 3.5 -uthr 4.5 -bin -mul 523 rh_HIP_tail


# Combine
fslmaths cort_space-MNI152NLin6Asym_res-02_dseg \
	-add thal_lo \
	-add lh_HIP_head_m -add lh_HIP_head_l -add lh_HIP_body -add lh_HIP_tail \
	-add rh_HIP_head_m -add rh_HIP_head_l -add rh_HIP_body -add rh_HIP_tail \
	atlas-MMPthalnuc_space-MNI152NLin6Asym_res-02_dseg

rm *HIP*.nii.gz

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
cat << EOF > thalhipp_dseg.tsv
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
420	lh_HIP_head_m
421	lh_HIP_head_l
422	lh_HIP_body
423	lh_HIP_tail
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
520	rh_HIP_head_m
521	rh_HIP_head_l
522	rh_HIP_body
523	rh_HIP_tail
EOF

# Make the complete label list
cat cort_dseg.tsv thalhipp_dseg.tsv > atlas-MMPthalnuc_dseg.tsv
