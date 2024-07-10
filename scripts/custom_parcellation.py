#!/usr/bin/env python
#
# Custom parcellation for XCP_D, following
# https://github.com/PennLINC/xcp_d-examples/blob/main/custom_parcellation.ipynb

import argparse
import bids
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
# mask_niigz       :   fmriprep func/NNN_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz
# fmri_niigz       :   xcpd func/NNN_space-MNI152NLin2009cAsym_desc-denoised_bold.nii.gz
# atlas_niigz      :   custom atlas in the same space as the mask, fmri images
# atlaslabels_tsv  :   atlas labels. Columns are numerical 'index' and text 'label'
# min_coverage     :   should match the param given for the xcpd run

parser = argparse.ArgumentParser()
parser.add_argument('--mask_niigz', required=True)
parser.add_argument('--fmri_niigz', required=True)
parser.add_argument('--atlas_niigz', required=True)
parser.add_argument('--atlaslabels_tsv', required=True)
parser.add_argument('--min_coverage', type=float, default=0.5)
parser.add_argument('--out_dir', required=True)
args = parser.parse_args()

## Parse the atlas label from the atlas filename
ents_atlas = bids.layout.parse_file_entities(args.atlas_niigz)
ents_mask = bids.layout.parse_file_entities(args.mask_niigz)
ents_fmri = bids.layout.parse_file_entities(args.fmri_niigz)

print(ents_atlas)
print(ents_fmri)

# Verify that spaces match
if ents_atlas.space != ents_fmri.space:
    raise Exception('Non-matching space for atlas and fmri')
if ents_atlas.space != ents_mask.space:
    raise Exception('Non-matching space for atlas and mask')


## Warp the atlas to the same space as the BOLD file
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
warpedatlas_niigz = warp_results.outputs.output_image


## Parcellate the BOLD file
# The preprocessed image from XCP_D will be censored already, if censoring is enabled.
# But the 'exact' number of volumes approach would need to be implemented here if wanted.
interface = NiftiParcellate(
    filtered_file=args.fmri_niigz,
    mask=args.mask_niigz,
    atlas=warpedatlas_niigz,
    atlas_labels=args.atlaslabels_tsv,
    min_coverage=args.min_coverage,
)
results = interface.run()
coverage_tsv = results.outputs.coverage
timeseries_tsv = results.outputs.timeseries

interface2 = TSVConnect(
    timeseries=results.outputs.timeseries,
    )
results2 = interface2.run()
correlations_tsv = results2.outputs.correlations

# Set output filenames according to xcpd scheme and put in xcpd location

# Example:
# NNN = sub-SUB_ses-SES_task-TASK_run-RUN_space-MNI152NLin2009cAsym

#   atlases/atlas-Glasser/atlas-Glasser_space-MNI152NLin2009cAsym_dseg.nii.gz
#   func/NNN_seg-Glasser_stat-coverage_bold.tsv
#   func/NNN_seg-Glasser_stat-mean_timeseries.tsv
#   func/NNN_seg-Glasser_stat-pearsoncorrelation_relmat.tsv


# FIXME ALFF and REHO?
# func/NNN_seg-Glasser_stat-alff_bold.tsv
# func/NNN_seg-Glasser_stat-reho_bold.tsv

