#!/usr/bin/env python
#
# Custom parcellation for XCP_D, following
# https://github.com/PennLINC/xcp_d-examples/blob/main/custom_parcellation.ipynb

import argparse
import bids
import os
import sys

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
parser.add_argument('--fmriprep_dir', required=True)
parser.add_argument('--xcpd_dir', required=True)
parser.add_argument('--space', default='MNI152NLin2009cAsym')
parser.add_argument('--atlas', required=True)
parser.add_argument('--atlas_dir', required=True)
parser.add_argument('--task', default='rest')
parser.add_argument('--run', default='1')
parser.add_argument('--min_coverage', type=float, default=0.5)
parser.add_argument('--out_dir', required=True)
args = parser.parse_args()

# Parse BIDS structures
bids_fmriprep = bids.layout.BIDSLayout(args.fmriprep_dir, validate=False)
bids_xcpd = bids.layout.BIDSLayout(args.xcpd_dir, validate=False)
bids_atlas = bids.layout.BIDSLayout(args.atlas_dir, validate=False, derivatives=True)


# Find input files
atlas_niigz = bids_atlas.get(
    space=args.space,
    atlas=args.atlas,
    suffix='dseg',
    extension='.nii.gz',
    )
if len(atlas_niigz)!=1:
    raise Exception(f'Found {len(atlas_niigz)} atlas .nii.gz instead of 1')
atlas_niigz = atlas_niigz[0]

atlas_tsv = bids_atlas.get(
    atlas=args.atlas,
    suffix='dseg',
    extension='.tsv',
    )
if len(atlas_tsv)!=1:
    raise Exception(f'Found {len(atlas_tsv)} atlas .tsv instead of 1')
atlas_tsv = atlas_tsv[0]

fmri_niigz = bids_xcpd.get(
    space=args.space,
    extension='.nii.gz',
    desc='denoised',
    suffix='bold',
    task=args.task,
    run=args.run,
    )
if len(fmri_niigz)!=1:
    raise Exception(f'Found {len(fmri_niigz)} fmri .nii.gz instead of 1')
fmri_niigz = fmri_niigz[0]

mask_niigz = bids_fmriprep.get(
    space=args.space,
    extension='.nii.gz',
    desc='brain',
    suffix='mask',
    task=args.task,
    run=args.run,
    )
if len(mask_niigz)!=1:
    raise Exception(f'Found {len(mask_niigz)} mask .nii.gz instead of 1')
mask_niigz = mask_niigz[0]


print(atlas_niigz.path)
print(atlas_tsv.path)
print(fmri_niigz.path)
print(mask_niigz.path)


sys.exit(0)
# FIXME Verify we only have 1 of everything and pull objects out of list


## Warp the atlas to the same space as the BOLD file
transform_files = get_std2bold_xfms(fmri_niigz)

grab_first_volume = IndexImage(in_file=fmri_niigz, index=0)
gfv_results = grab_first_volume.run()

warp_atlases_to_bold_space = ApplyTransforms(
    interpolation="GenericLabel",
    input_image_type=3,
    dimension=3,
    reference_image=gfv_results.outputs.out_file,
    input_image=atlas_niigz,
    transforms=transform_files,
)
warp_results = warp_atlases_to_bold_space.run()
warpedatlas_niigz = warp_results.outputs.output_image


## Parcellate the BOLD file
# The preprocessed image from XCP_D will be censored already, if censoring is enabled.
# But the 'exact' volumes approach would need to be implemented here if wanted.
interface = NiftiParcellate(
    filtered_file=fmri_niigz,
    mask=mask_niigz,
    atlas=warpedatlas_niigz,
    atlas_labels=atlas_tsv,
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

# Set output filenames according to xcpd scheme and put in xcpd location. Use bidslayout tools for write

# Example:
# NNN = sub-SUB_ses-SES_task-TASK_run-RUN_space-MNI152NLin2009cAsym

#   atlases/atlas-Glasser/atlas-Glasser_space-MNI152NLin2009cAsym_dseg.nii.gz   # Sampling matches preprocessed func
#   func/NNN_seg-Glasser_stat-coverage_bold.tsv
#   func/NNN_seg-Glasser_stat-mean_timeseries.tsv
#   func/NNN_seg-Glasser_stat-pearsoncorrelation_relmat.tsv


# FIXME ALFF and REHO?
# func/NNN_seg-Glasser_stat-alff_bold.tsv
# func/NNN_seg-Glasser_stat-reho_bold.tsv

