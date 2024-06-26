#!/usr/bin/env python
#
# Custom parcellation for XCP_D, following
# https://github.com/PennLINC/xcp_d-examples/blob/main/custom_parcellation.ipynb

import argparse
import os

from xcp_d.interfaces.ants import ApplyTransforms
from xcp_d.interfaces.connectivity import NiftiParcellate
from xcp_d.interfaces.nilearn import IndexImage
from xcp_d.utils.utils import get_std2bold_xfms


parser = argparse.ArgumentParser()
parser.add_argument('--mask_niigz', required=True)
parser.add_argument('--temporalmask_tsv', required=True)
parser.add_argument('--fmri_niigz', required=True)
parser.add_argument('--atlas_niigz', required=True)
parser.add_argument('--atlaslabels_tsv', required=True)
parser.add_argument('--min_coverage', default=0.5)
args = parser.parse_args()


#xcpd_dir = "/Users/taylor/Documents/datasets/ds003643/derivatives/xcp_d/sub-EN100/func"
#fmriprep_dir = "/Users/taylor/Documents/datasets/ds003643/derivatives/fmriprep/sub-EN100/func"

#mask = os.path.join(fmriprep_dir, "sub-EN100_task-lppEN_run-1_space-MNI152NLin6Asym_desc-brain_mask.nii.gz")
#temporal_mask = os.path.join(xcpd_dir, "sub-EN100_task-lppEN_run-1_outliers.tsv")

#min_coverage = 0.5  # use the same threshold you used for the XCP-D call
#correlate = True

#nifti_file = os.path.join(xcpd_dir, "sub-EN100_task-lppEN_run-1_space-MNI152NLin6Asym_desc-denoised_bold.nii.gz")
#nifti_atlas = "tpl-MNI152NLin6Asym_atlas-Schaefer2018v0143_res-02_desc-100Parcels17Networks_dseg.nii.gz"

# Step 1. Mock up an atlas labels file
# The file must have two columns: index and label
# I decided to just use one of the ones from XCP-D.
#nifti_atlas_labels = "atlas-Schaefer2018v0143_desc-100Parcels17Networks_dseg.tsv"



# Step 2. Warp the atlas to the same space as the BOLD file
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

# Step 3. Parcellate the BOLD file
interface = NiftiParcellate(
    filtered_file=args.fmri_niigz,
    mask=args.mask_niigz,
    temporal_mask=args.temporalmask_tsv,
    atlas=warped_atlas_niigz,
    atlas_labels=args.atlaslabels_tsv,
    min_coverage=args.min_coverage,
    correlate=True,
)
results = interface.run()

# These are your outputs
timeseries_file = results.outputs.timeseries
correlations_file = results.outputs.correlations

