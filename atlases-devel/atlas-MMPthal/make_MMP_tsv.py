#!/usr/bin/env python
#
# Right hemisphere labels are given in atlas-MMP_detailedinfo.csv. For left
# hemisphere corresponding label, add 180.

import pandas

info = pandas.read_csv('atlas-MMP_detailedinfo.csv', usecols=[0, 1])

out_index = (
    info['Parcellation Index'].to_list() + 
    [x+180 for x in info['Parcellation Index'].to_list()]
    )

out_label = (
    ['rh_' + x for x in info['Area Name'].to_list()] +
    ['lh_' + x for x in info['Area Name'].to_list()]
    )

out_info = pandas.DataFrame(
    list(zip(out_index, out_label)),
    columns=('index', 'label')
    )

out_info.to_csv('atlas-MMP_dseg.tsv', sep='\t', index=False)
