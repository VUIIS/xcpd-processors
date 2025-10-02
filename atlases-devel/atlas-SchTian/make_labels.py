#!/usr/bin/env python

import pandas

tian = pandas.read_csv('Tian_Subcortex_S3_3T_label.txt', header=None, names=['label'])
tian['index'] = [x+2000 for x in range(1, tian.shape[0]+1)]

s200 = pandas.read_csv(
    'Schaefer2018_200Parcels_7Networks_order.lut', 
    sep=' ', 
    header=None, 
    names=['index','a','b','c','label'],
    )
all200 = pandas.concat(
    [s200[['index','label']],
    tian[['index','label']]]
    )
all200.to_csv('atlas-Sch200Tian_dseg.tsv', sep='\t', index=False)

s400 = pandas.read_csv(
    'Schaefer2018_400Parcels_7Networks_order.lut', 
    sep=' ', 
    header=None, 
    names=['index','a','b','c','label'],
    )
all400 = pandas.concat(
    [s400[['index','label']],
    tian[['index','label']]]
    )
all400.to_csv('atlas-Sch400Tian_dseg.tsv', sep='\t', index=False)
