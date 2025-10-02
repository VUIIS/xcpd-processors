#!/usr/bin/env bash

# Check for overlap - output should be max 1 but is max 2 so there is overlap.
# Overlaid on the standard T1, the overlapping voxels look like they should be 
# assigned to the cortex (Schaeffer).
fslmaths Schaefer2018_200Parcels_7Networks_order_FSLMNI152_1mm -bin tmpS
fslmaths Tian_Subcortex_S3_3T_1mm -bin tmpT
fslmaths tmpS -add tmpT tmpBoth
fslmaths tmpBoth -thr 2 overlap
rm -f tmp*.nii.gz
fslstats overlap -R

# Make Schaeffer mask to remove from Tian (200 and 400 cover the same voxels)
fslmaths Schaefer2018_200Parcels_7Networks_order_FSLMNI152_1mm -bin mask_schaeffer
fslmaths mask_schaeffer -sub 1 -mul -1 antimask_schaeffer
fslmaths Tian_Subcortex_S3_3T_1mm -mul antimask_schaeffer Tian_Subcortex_S3_3T_1mm_masked

# Tian mask
fslmaths Tian_Subcortex_S3_3T_1mm_masked -bin mask_tian

# Check again for overlap
fslmaths mask_schaeffer -add mask_tian mask_both
fslmaths mask_both -thr 2 overlap_masked
fslstats overlap_masked -R

# Add 2000 to Tian and combine
fslmaths Tian_Subcortex_S3_3T_1mm_masked \
    -add 2000 -mul mask_tian \
    -add Schaefer2018_200Parcels_7Networks_order_FSLMNI152_1mm \
    atlas-Sch200Tian_space-MNI152NLin6Asym_res-01_dseg

fslmaths Tian_Subcortex_S3_3T_1mm_masked \
    -add 2000 -mul mask_tian \
    -add Schaefer2018_400Parcels_7Networks_order_FSLMNI152_1mm \
    atlas-Sch400Tian_space-MNI152NLin6Asym_res-01_dseg

