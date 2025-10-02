#!/usr/bin/env bash

# Check for overlap - output should be max 1 but is max 2 so there is overlap.
# Overlaid on the standard T1, the overlapping voxels look like they should be 
# assigned to the cortex (Schaeffer).
fslmaths Schaefer2018_200Parcels_7Networks_order_FSLMNI152_1mm -bin tmpS
fslmaths Tian_Subcortex_S3_3T_1mm -bin tmpT
fslmaths tmpS -add tmpT tmpBoth
fslstats tmpBoth -R
