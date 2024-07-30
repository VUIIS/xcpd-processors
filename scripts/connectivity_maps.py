#!/usr/bin/env python
#
# Connectivity maps for ROIs in XCP_D output
#
# We need these to be in a specified space/resolution so they 
# match across subjects/sessions. We will resample computed 
# connmaps to the grid of the chosen atlas.

import argparse
import bids
import nibabel
import nibabel.processing
import nitime
import nitime.fmri
import nitime.analysis
import numpy
import os
import pandas
import re
import shutil
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
parser.add_argument('--seeds', required=False, nargs='*',
    help='List of seed region names, space separated. All if not specified')
parser.add_argument('--saveR', action='store_true',
    help='Save R maps')
parser.add_argument('--saveZ', action='store_true',
    help='Save Z maps')
parser.add_argument('--fwhm', default=0, nargs='*', type=int, 
    help='List of smoothing kernels, space separated. Default 0 (no smoothing)')
args = parser.parse_args()

if not args.saveR and not args.saveZ:
    raise exception('No maps specified. Use --saveR or --saveZ')


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
fmri_tr = fmri_img.header['pixdim'][4]

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



## https://nipy.org/nitime/examples/seed_analysis.html


# We need voxel coords to stow correlations in the right place
volume_shape = fmri_img.shape[:-1]
coords = list(numpy.ndindex(volume_shape))
coords_target = numpy.array(coords).T
coords_indices = list(coords_target)

# Load ROI time series from tsv
roi_data = pandas.read_csv(fmri_tsv, sep='\t')
nroi = roi_data.shape[1]

# Load preprocessed fmri in nitime format
fmri_timeseries = nitime.fmri.io.time_series_from_file(
    fmri_niigz.path,
    coords_target,
    TR=fmri_tr,
    )


# Compute correlations

# Region label for filename alphanum only. Cannot start with digit
def sanitize_seedname(seedname):
    newname = re.sub('^([0-9])', 'x\g<1>', seedname)
    newname = re.sub('[^0-9A-Za-z]', '', newname)
    if newname!=seedname:
        print(f'Renaming seed {seedname} to {newname} for connmap nii.gz')
    return newname
    
# Base filename info
ents = {
    'subject': fmri_niigz.get_entities()['subject'],
    'session': fmri_niigz.get_entities()['session'],
    'task': fmri_niigz.get_entities()['task'],
    'run': fmri_niigz.get_entities()['run'],
    'space': args.space,
    'seg': args.atlas,
    'extension': 'nii.gz',
    }
pattern = (
    'sub-{subject}/ses-{session}/func/'
    'sub-{subject}_ses-{session}_task-{task}_run-{run}_space-{space}_seg-{seg}_stat-{stat}_{suffix}{extension}'
    )

# Compute and save for each ROI
# Ref for indexing: https://stackoverflow.com/questions/19821425/how-to-filter-numpy-array-by-list-of-indices
for r in range(nroi):
    roi_name = roi_data.columns[r]
    if args.seeds and not roi_name in args.seeds:
        continue
    roi_timeseries = nitime.timeseries.TimeSeries(
        roi_data[roi_name].transpose(), 
        sampling_interval=fmri_tr,
        )
    analyzer = nitime.analysis.SeedCorrelationAnalyzer(roi_timeseries, fmri_timeseries)
    q = analyzer.corrcoef
    connmapR = numpy.empty(volume_shape)
    connmapR[tuple(coords_indices)] = analyzer.corrcoef
    connmapR[numpy.isnan(connmapR)] = 0

    if args.saveR:
        for kern in args.fwhm:
            connmapR_img = nibabel.Nifti1Image(connmapR, fmri_img.affine)
            if kern>0:
                connmapR_img = nibabel.processing.smooth_image(connmapR_img, kern)
                ents['stat'] = f'Rs{kern}'
            else:
                ents['stat'] = 'R'
            with tempfile.TemporaryDirectory() as tmp_dir:
                nibabel.save(connmapR_img, os.path.join(tmp_dir, 'connmapR.nii.gz'))
                warp_fmri_to_atlas_space = ApplyTransforms(
                    interpolation="Linear",
                    input_image_type=3,
                    dimension=3,
                    reference_image=atlas_niigz.path,
                    input_image=os.path.join(tmp_dir, 'connmapR.nii.gz'),
                    output_image=os.path.join(tmp_dir, 'rconnmapR.nii.gz'),
                    transforms='identity',
                    )
                warp_results = warp_fmri_to_atlas_space.run()
                warpedfmri_niigz = warp_results.outputs.output_image
                ents['suffix'] = sanitize_seedname(roi_name)
                connmapR_niigz = bids_xcpd.build_path(ents, pattern, validate=False)
                shutil.copyfile(warpedfmri_niigz, connmapR_niigz)

    if args.saveZ:
        ntimepoints = roi_timeseries.shape[-1]
        connmapZ = numpy.arctanh(connmapR) * numpy.sqrt(ntimepoints - 3)
        
        for kern in args.fwhm:
            connmapZ_img = nibabel.Nifti1Image(connmapZ, fmri_img.affine)
            if kern>0:
                connmapZ_img = nibabel.processing.smooth_image(connmapZ_img, kern)
                ents['stat'] = f'Zs{kern}'
            else:
                ents['stat'] = 'Z'
            with tempfile.TemporaryDirectory() as tmp_dir:
                nibabel.save(connmapZ_img, os.path.join(tmp_dir, 'connmapZ.nii.gz'))
                warp_fmri_to_atlas_space = ApplyTransforms(
                    interpolation="Linear",
                    input_image_type=3,
                    dimension=3,
                    reference_image=atlas_niigz.path,
                    input_image=os.path.join(tmp_dir, 'connmapZ.nii.gz'),
                    output_image=os.path.join(tmp_dir, 'rconnmapZ.nii.gz'),
                    transforms='identity',
                    )
                warp_results = warp_fmri_to_atlas_space.run()
                warpedfmri_niigz = warp_results.outputs.output_image
                ents['suffix'] = sanitize_seedname(roi_name)
                connmapZ_niigz = bids_xcpd.build_path(ents, pattern, validate=False)
                shutil.copyfile(warpedfmri_niigz, connmapZ_niigz)
