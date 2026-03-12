#!/usr/bin/env python
#
# Stats file conversions for XCP_D when standard atlas used

import argparse
import bids
import os
import pandas
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--xcpd_dir', required=True, 
    help='Absolute path of xcpd output (must match subject/session/etc of fmriprep)')
parser.add_argument('--out_dir', default='/OUTPUTS', 
    help='Output directory for QC CSV')
args = parser.parse_args()

# Process BIDS dir
bids_xcpd = bids.layout.BIDSLayout(args.xcpd_dir, validate=False)

# Find QC file and convert to CSV
# Fail if more than one because we can't handle that right now
qc_tsv = bids_xcpd.get(
    extension='tsv',
    desc='linc',
    suffix='qc',
    )
if len(qc_tsv)!=1:
    raise Exception(f'Found {len(qc_tsv)} qc .tsv instead of 1')
qc_tsv = qc_tsv[0]
qc = qc_tsv.get_df()
qc.to_csv(os.path.join(args.out_dir, 'qc.csv'), index=False)
