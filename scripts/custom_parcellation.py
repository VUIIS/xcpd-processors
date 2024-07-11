#!/usr/bin/env python
#
# Custom parcellation for XCP_D, following
# https://github.com/PennLINC/xcp_d-examples/blob/main/custom_parcellation.ipynb

import argparse
import bids
import os
import sys
import tempfile

from xcp_d.interfaces.ants import ApplyTransforms
from xcp_d.interfaces.connectivity import NiftiParcellate, TSVConnect
from xcp_d.interfaces.nilearn import IndexImage
from xcp_d.utils.utils import get_std2bold_xfms

parser = argparse.ArgumentParser()
parser.add_argument('--fmriprep_dir', required=True, 
    help='Location of fmriprep (for brain mask)')
parser.add_argument('--xcpd_dir', required=True, 
    help='Location of xcpd output (must match subject/session/etc of fmriprep)')
parser.add_argument('--space', default='MNI152NLin2009cAsym', 
    help='Space to use if multiple (default to MNI152NLin2009cAsym)')
parser.add_argument('--atlas', required=True, 
    help='Name of atlas to use')
parser.add_argument('--atlas_dir', required=True, 
    help='Where atlas and label file are found')
parser.add_argument('--task', default='rest', 
    help='Which task to use if multiple present (default to rest)')
parser.add_argument('--run', default='1', 
    help='Which run to use (default to 1)')
parser.add_argument('--min_coverage', type=float, default=0.5, 
    help='Should match the param given for the xcpd run')
args = parser.parse_args()

# FIXME Change to temp dir later
#with tempfile.TemporaryDirectory() as tmpdirname:
#     print('created temporary directory', tmpdirname)
os.chdir('../OUTPUTS')


# Parse BIDS structures
bids_fmriprep = bids.layout.BIDSLayout(args.fmriprep_dir, validate=False)
bids_xcpd = bids.layout.BIDSLayout(args.xcpd_dir, validate=False)
bids_atlas = bids.layout.BIDSLayout(args.atlas_dir, validate=False)


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



## Warp the atlas to the same space as the BOLD file
transform_files = get_std2bold_xfms(fmri_niigz.path)

grab_first_volume = IndexImage(in_file=fmri_niigz.path, index=0)
gfv_results = grab_first_volume.run()

warp_atlases_to_bold_space = ApplyTransforms(
    interpolation="GenericLabel",
    input_image_type=3,
    dimension=3,
    reference_image=gfv_results.outputs.out_file,
    input_image=atlas_niigz.path,
    transforms=transform_files,
)
warp_results = warp_atlases_to_bold_space.run()
warpedatlas_niigz = warp_results.outputs.output_image


## Parcellate the BOLD file
# The preprocessed image from XCP_D will be censored already, if censoring is enabled.
# But the 'exact' volumes approach would need to be implemented here if wanted.
interface = NiftiParcellate(
    filtered_file=fmri_niigz.path,
    mask=mask_niigz.path,
    atlas=warpedatlas_niigz,
    atlas_labels=atlas_tsv.path,
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

# FIXME Set output filenames according to xcpd scheme and put in xcpd location. Use bidslayout tools for write

atlas_ents = {
    'atlas': args.atlas,
    'space': args.space,
    'suffix': 'dseg',
    'extension': '.nii.gz',
    }
atlas_pattern = (
    'atlases/atlas-{atlas}/'
    'atlas-{atlas}_space-{space}_{suffix}{extension}'
    )
atlas_path = bids_xcpd.build_path(atlas_ents, atlas_pattern, validate=False)

base_ents = {
    'subject': fmri_niigz.get_entities()['subject'],
    'session': fmri_niigz.get_entities()['session'],
    'task': args.task,
    'run': args.run,
    'space': args.space,
    'seg': args.atlas,
    }

cov_ents = base_ents
cov_ents['stat'] = 'coverage'
cov_ents['suffix'] = 'bold'
cov_ents['extension'] = 'tsv'
cov_pattern = (
    'sub-{subject}/ses-{session}/func/'
    'sub-{subject}_ses-{session}_task-{task}_run-{run}_space-{space}_seg-{seg}_stat-{stat}_{suffix}{extension}'
    )
cov_path = bids_xcpd.build_path(cov_ents, cov_pattern, validate=False)

ts_ents = base_ents
ts_ents['stat'] = 'mean'
ts_ents['suffix'] = 'timeseries'
ts_ents['extension'] = 'tsv'
ts_pattern = (
    'sub-{subject}/ses-{session}/func/'
    'sub-{subject}_ses-{session}_task-{task}_run-{run}_space-{space}_seg-{seg}_stat-{stat}_{suffix}{extension}'
    )
ts_path = bids_xcpd.build_path(ts_ents, ts_pattern, validate=False)

cor_ents = base_ents
cor_ents['stat'] = 'pearsoncorrelation'
cor_ents['suffix'] = 'relmat'
cor_ents['extension'] = 'tsv'
cor_pattern = (
    'sub-{subject}/ses-{session}/func/'
    'sub-{subject}_ses-{session}_task-{task}_run-{run}_space-{space}_seg-{seg}_stat-{stat}_{suffix}{extension}'
    )
cor_path = bids_xcpd.build_path(cor_ents, cor_pattern, validate=False)


bids_xcpd.write_to_file(atlas_path, copy_from=warpedatlas_niigz)
bids_xcpd.write_to_file(cov_path, copy_from=coverage_tsv)
bids_xcpd.write_to_file(ts_path, copy_from=timeseries_tsv)
bids_xcpd.write_to_file(cor_path, copy_from=correlations_tsv)


# Outputs are stored in the working directory
# correlations.tsv                        Connectivity matrix
# coverage.tsv                            Coverage for each ROI in the fMRI image
# img_3d.nii.gz                           First fMRI volume (not needed again)
# timeseries.tsv                          Extracted preprocessed ROI time series
# NNN_atlas-CC20240607_dseg_trans.nii.gz  Resampled atlas


# Example:
# NNN = sub-SUB_ses-SES_task-TASK_run-RUN_space-MNI152NLin2009cAsym

#   atlases/atlas-Glasser/atlas-Glasser_space-MNI152NLin2009cAsym_dseg.nii.gz   # Sampling matches preprocessed func
#   func/NNN_seg-Glasser_stat-coverage_bold.tsv
#   func/NNN_seg-Glasser_stat-mean_timeseries.tsv
#   func/NNN_seg-Glasser_stat-pearsoncorrelation_relmat.tsv


# FIXME ALFF and REHO?
# func/NNN_seg-Glasser_stat-alff_bold.tsv
# func/NNN_seg-Glasser_stat-reho_bold.tsv

