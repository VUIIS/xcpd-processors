#!/usr/bin/env python
#
# Custom parcellation for XCP_D, following
# https://github.com/PennLINC/xcp_d-examples/blob/main/custom_parcellation.ipynb

import argparse
import bids
import os
import pandas
import sys
import tempfile

from xcp_d.interfaces.ants import ApplyTransforms
from xcp_d.interfaces.connectivity import NiftiParcellate, TSVConnect
from xcp_d.interfaces.nilearn import IndexImage
from xcp_d.utils.utils import get_std2bold_xfms

parser = argparse.ArgumentParser()
parser.add_argument('--fmriprep_dir', required=True, 
    help='Absolute path of fmriprep output (for brain mask)')
parser.add_argument('--xcpd_dir', required=True, 
    help='Absolute path of xcpd output (must match subject/session/etc of fmriprep)')
parser.add_argument('--space', default='MNI152NLin2009cAsym', 
    help='Space to use if multiple (default to MNI152NLin2009cAsym)')
parser.add_argument('--atlas', required=True, 
    help='Name of atlas to use')
parser.add_argument('--task', 
    help='Which task to use if multiple present (CURRENTLY IGNORED)')
parser.add_argument('--run', 
    help='Which run to use if multiple present (CURRENTLY IGNORED)')
parser.add_argument('--min_coverage', type=float, default=0.5, 
    help='Should match the param given for the xcpd run')
parser.add_argument('--out_dir', default='/OUTPUTS', 
    help='Output directory for stats CSVs')
args = parser.parse_args()

# Work in a temporary directory since some functions don't allow us
# to specify output location of working files.
out_dir = tempfile.TemporaryDirectory()
os.chdir(out_dir.name)

# Find atlas dir
atlas_dir = os.path.realpath(os.path.join(sys.path[0], '..', 'atlases'))

# Parse BIDS structures
bids_fmriprep = bids.layout.BIDSLayout(args.fmriprep_dir, validate=False)
bids_xcpd = bids.layout.BIDSLayout(args.xcpd_dir, validate=False)
bids_atlas = bids.layout.BIDSLayout(atlas_dir, validate=False)


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
    )
if len(fmri_niigz)!=1:
    raise Exception(f'Found {len(fmri_niigz)} fmri .nii.gz instead of 1')
fmri_niigz = fmri_niigz[0]

mask_niigz = bids_fmriprep.get(
    space=args.space,
    extension='.nii.gz',
    desc='brain',
    suffix='mask',
    task=fmri_niigz.get_entities()['task'],
    run=fmri_niigz.get_entities()['run'],
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

# Write outputs to file in the existing XCPD structure

# Set up base entities. Note we are re-using ents and pattern vars so order of stuff matters
ents = {
    'subject': fmri_niigz.get_entities()['subject'],
    'session': fmri_niigz.get_entities()['session'],
    'task': fmri_niigz.get_entities()['task'],
    'run': fmri_niigz.get_entities()['run'],
    'space': args.space,
    'seg': args.atlas,
    }

# Write resampled atlas image
ents['atlas'] = args.atlas
ents['suffix'] = 'dseg'
ents['extension'] = 'nii.gz'
pattern = (
    'atlases/atlas-{atlas}/'
    'atlas-{atlas}_space-{space}_{suffix}{extension}'
    )
bids_xcpd.write_to_file(ents, pattern, copy_from=warpedatlas_niigz, validate=False)

# Write atlas labels
ents['extension'] = 'tsv'
pattern = (
    'atlases/atlas-{atlas}/'
    'atlas-{atlas}_{suffix}{extension}'
    )
bids_xcpd.write_to_file(ents, pattern, copy_from=atlas_tsv, validate=False)

# Write coverage tsv
ents['stat'] = 'coverage'
ents['suffix'] = 'bold'
ents['extension'] = 'tsv'
pattern = (
    'sub-{subject}/ses-{session}/func/'
    'sub-{subject}_ses-{session}_task-{task}_run-{run}_space-{space}_seg-{seg}_stat-{stat}_{suffix}{extension}'
    )
bids_xcpd.write_to_file(ents, pattern, copy_from=coverage_tsv, validate=False)
final_coverage_tsv = bids_xcpd.build_path(ents, pattern, validate=False)

# Write timeseries tsv
ents['stat'] = 'mean'
ents['suffix'] = 'timeseries'
ents['extension'] = 'tsv'
bids_xcpd.write_to_file(ents, pattern, copy_from=timeseries_tsv, validate=False)

# Write corr matrix
ents['stat'] = 'pearsoncorrelation'
ents['suffix'] = 'relmat'
ents['extension'] = 'tsv'
bids_xcpd.write_to_file(ents, pattern, copy_from=correlations_tsv, validate=False)

# Clean up temp files
out_dir.cleanup()

# Convert a couple of things to sync-friendly csv
qc_tsv = bids_xcpd.get(
    extension='tsv',
    desc='linc',
    suffix='qc',
    )
if len(qc_tsv)!=1:
    raise Exception(f'Found {len(qc_tsv)} qc .tsv instead of 1')
qc = qc_tsv[0].get_df()
qc.to_csv(os.path.join(args.out_dir, 'qc.csv'), index=False)

cov = pandas.read_csv(final_coverage_tsv, sep='\t')
cov.transpose().to_csv(os.path.join(args.out_dir, 'coverage.csv'), index=False, header=False)


# FIXME ALFF and REHO? E.g.
# func/NNN_seg-Glasser_stat-alff_bold.tsv
# func/NNN_seg-Glasser_stat-reho_bold.tsv

