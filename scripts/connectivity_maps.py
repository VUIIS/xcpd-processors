#!/usr/bin/env python
#
# Connectivity maps for ROIs in XCP_D output
#
# We need these to be in a specified space/resolution so they 
# match across subjects/sessions. We could enforce the grid of
# the atlas, but that means resampling the preprocessed fmri -
# can we modify xcpd get_bold2std_and_t1w_xfms for that? See
# for usage
# https://github.com/PennLINC/xcp_d/blob/30c7e01366d925b352573bcb207ad84d7c7dae74/xcp_d/workflows/plotting.py#L172
#
# Or, we could rely on fmriprep having been run with a specified
# resolution grid.

import argparse
import bids
import os
import nibabel
import nitime
import nitime.fmri
import nitime.analysis
import pandas
import sys
import tempfile
from xcp_d.interfaces.ants import ApplyTransforms


parser = argparse.ArgumentParser()
parser.add_argument('--xcpd_dir', required=True, 
    help='Absolute path of xcpd output')
parser.add_argument('--space', default='MNI152NLin2009cAsym', 
    help='Space to use if multiple (default to MNI152NLin2009cAsym)')
parser.add_argument('--atlas', required=True, 
    help='Name of atlas to use')
args = parser.parse_args()

# Work in a temporary directory since some functions don't allow us
# to specify output location of working files.
#out_dir = tempfile.TemporaryDirectory()
#os.chdir(out_dir.name)

# Find atlas dir
atlas_dir = os.path.realpath(os.path.join(sys.path[0], '..', 'atlases'))

# Parse BIDS structures
bids_xcpd = bids.layout.BIDSLayout(args.xcpd_dir, validate=False)
bids_atlas = bids.layout.BIDSLayout(atlas_dir, validate=False)


# Find input files. We specify the space for both fmri and atlas
# so they will be the same, which is needed when we later assume
# 'identity' when applying the transform.
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
fmri_img = nibabel.load(fmri_niigz.path)

ents = {
    'subject': fmri_niigz.get_entities()['subject'],
    'session': fmri_niigz.get_entities()['session'],
    'task': fmri_niigz.get_entities()['task'],
    'run': fmri_niigz.get_entities()['run'],
    'space': args.space,
    'seg': args.atlas,
    'stat': 'mean',
    'suffix': 'timeseries',
    'extension': 'tsv',
    }
pattern = (
    'sub-{subject}/ses-{session}/func/'
    'sub-{subject}_ses-{session}_task-{task}_run-{run}_space-{space}_seg-{seg}_stat-{stat}_{suffix}{extension}'
    )
fmri_tsv = bids_xcpd.build_path(ents, pattern, validate=False)



# Load extracted ROI timeseries from TSV, convert to nitime format
# https://nipy.org/nitime/examples/seed_analysis.html
roi_timeseries = nitime.timeseries.TimeSeries(
    pandas.read_csv(fmri_tsv, sep='\t').transpose(), 
    sampling_interval=fmri_img.header['pixdim'][4],
    )

# Load preprocessed fmri in nitime format
fmri_timeseries = nitime.fmri.io.time_series_from_file(
    fmri_niigz.path, 
    TR=fmri_img.header['pixdim'][4],
    )

# Compute correlations
corrmaps = nitime.analysis.SeedCorrelationAnalyzer(roi_timeseries, fmri_timeseries)

print(corrmaps)


sys.exit(0)

## Resample the connectivity maps to the same grid as the atlas
warp_fmri_to_atlas_space = ApplyTransforms(
    interpolation="Linear",
    input_image_type=3,
    dimension=3,
    reference_image=atlas_niigz.path,
    input_image=fmri_niigz.path,
    transforms='identity',
)
warp_results = warp_fmri_to_atlas_space.run()
warpedfmri_niigz = warp_results.outputs.output_image
print(warpedfmri_niigz)

