#!/usr/bin/env python
#
# Custom parcellation for XCP_D, following
# https://github.com/PennLINC/xcp_d-examples/blob/main/custom_parcellation.ipynb

import argparse
import os

from xcp_d.interfaces.ants import ApplyTransforms
from xcp_d.interfaces.connectivity import NiftiParcellate, TSVConnect
from xcp_d.interfaces.nilearn import IndexImage
from xcp_d.utils.utils import get_std2bold_xfms

# Outputs are stored in the working directory
# correlations.tsv                        Connectivity matrix
# coverage.tsv                            Coverage for each ROI in the fMRI image
# img_3d.nii.gz                           First fMRI volume (not needed again)
# timeseries.tsv                          Extracted preprocessed ROI time series
# NNN_atlas-CC20240607_dseg_trans.nii.gz  Resampled atlas

## Step 1. Inputs
# mask_niigz       :   fmriprep func/NNN_space-MNI152NLin6Asym_desc-brain_mask.nii.gz
# temporalmask_tsv :   xcpd func/NNN_outliers.tsv, or "" to not use
# fmri_niigz       :   xcpd func/NNN_space-MNI152NLin2009cAsym_desc-denoised_bold.nii.gz
# atlas_niigz      :   custom atlas in the same space as the mask, fmri images
# atlaslabels_tsv  :   atlas labels. Columns are numerical 'index' and text 'label'
# min_coverage     :   should match the param given for the xcpd run

parser = argparse.ArgumentParser()
parser.add_argument('--mask_niigz', required=True)
parser.add_argument('--temporalmask_tsv', required=True)
parser.add_argument('--fmri_niigz', required=True)
parser.add_argument('--atlas_niigz', required=True)
parser.add_argument('--atlaslabels_tsv', required=True)
parser.add_argument('--min_coverage', type=float, default=0.5)
args = parser.parse_args()


## Step 2. Warp the atlas to the same space as the BOLD file
transform_files = get_std2bold_xfms(args.fmri_niigz)

grab_first_volume = IndexImage(in_file=args.fmri_niigz, index=0)
gfv_results = grab_first_volume.run()

warp_atlases_to_bold_space = ApplyTransforms(
    interpolation="GenericLabel",
    input_image_type=3,
    dimension=3,
    reference_image=gfv_results.outputs.out_file,
    input_image=args.atlas_niigz,
    transforms=transform_files,
)
warp_results = warp_atlases_to_bold_space.run()
warped_atlas_niigz = warp_results.outputs.output_image


## Step 3. Parcellate the BOLD file
#    temporal_mask=args.temporalmask_tsv,
interface = NiftiParcellate(
    filtered_file=args.fmri_niigz,
    mask=args.mask_niigz,
    atlas=warped_atlas_niigz,
    atlas_labels=args.atlaslabels_tsv,
    min_coverage=args.min_coverage,
)
results = interface.run()

interface2 = TSVConnect(
    timeseries=results.outputs.timeseries,
    )
results2 = interface2.run()

print(results.outputs)
print(results2.outputs)

# These are your outputs
#timeseries_file = results.outputs.timeseries
#correlations_file = results.outputs.correlations

