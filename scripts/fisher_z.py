#!/usr/bin/env python
#
# Convert XCP_D Pearson output to Fisher Z

import argparse
import bids
import numpy
import os
import pandas
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--xcpd_dir', required=True, 
    help='Absolute path of xcpd output (must match subject/session/etc of fmriprep)')
args = parser.parse_args()

# Parse BIDS structure
bids_xcpd = bids.layout.BIDSLayout(args.xcpd_dir, validate=False)

# Doesn't work - uniqueness conflict in datatype
#bids_xcpd = bids.layout.BIDSLayout(args.xcpd_dir, validate=False, config=['bids', 'xcp_d_bids_config.json'])

# Doesn't work - deprecated, and still doesn't grab stat or seg
#bids_xcpd = bids.layout.BIDSLayout(args.xcpd_dir, validate=False, config_filename='xcp_d_bids_config.json')

# Hack is to just get filename, replace pearsoncorrelation with fisherz, and be done

# Get all correlation files

# Get corresponding number of time points

# Load R, convert, save



# Find input files

corr_tsvs_all = bids_xcpd.get(
    extension='.tsv',
    suffix='relmat',
    )

# Stat is not a valid entity by default. It is defined here
# https://github.com/PennLINC/xcp_d/blob/main/xcp_d/data/xcp_d_bids_config.json
# But I don't know how to use that. So just manually reduce to list to only 
# pearsoncorrelation here
corr_tsvs = [x for x in corr_tsvs_all if x.endswith('stat-pearsoncorrelation_relmat.tsv')]

# Process them
for corr_tsv in corr_tsvs:
    
    # Create filenames
    fname = os.path.join(corr_tsv.dirname, corr_tsv.filename)
    timeseries_tsv = fname.replace('stat-pearsoncorrelation_relmat.tsv', 'stat-mean_timeseries.tsv')
    fisherz_tsv = fname.replace('stat-pearsoncorrelation_relmat.tsv', 'stat-fisherz_relmat.tsv')
    
    # Get the timeseries and compute DOF
    timeseries = pandas.read_csv(timeseries_tsv, sep='\t')
    ntimepoints = timeseries.shape[0]

    # Compute Fisher Z from R and save to file
    pearsonr = pandas.read_csv(corr_tsv, sep='\t', index_col=0)
    fisherz = numpy.arctanh(pearsonr) * numpy.sqrt(ntimepoints - 3)
    fisherz.to_csv(fisherz_tsv, sep='\t')
