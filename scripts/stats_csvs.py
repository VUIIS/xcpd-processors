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
parser.add_argument('--atlas', required=True, 
    help='Atlas used')
parser.add_argument('--out_dir', default='/OUTPUTS', 
    help='Output directory for stats CSVs')
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

# Find coverage file
# Base this on QC filename because 'stat' is not a valid standard BIDS
# entity and I don't know how to use the xcp-d extended entities
cov_tsv_fname = qc_tsv.path.replace(
    f'_desc-linc_qc.tsv',
    f'_seg-{args.atlas}_stat-coverage_bold.tsv'
)
cov = pandas.read_csv(cov_tsv_fname, sep='\t')
covdir = os.path.join(args.out_dir, 'COVERAGE')
os.makedirs(covdir, exist_ok=True)
cov.transpose().to_csv(
    os.path.join(covdir, f'coverage-{args.atlas}.csv'), 
    index=False, 
    header=False
    )
