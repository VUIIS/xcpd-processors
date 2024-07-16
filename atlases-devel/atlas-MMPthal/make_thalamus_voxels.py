#!/usr/bin/env python

import nibabel
import numpy
import pandas

# Enumerate thalamus voxels
img = nibabel.load('rthalmask.nii.gz')

num_nonzero = numpy.sum(img.get_fdata()>0)

newvals = img.get_fdata().copy()
inds = newvals>0

# Add 10000 so we don't overlap with other atlas
thalvals = [x + 10000 for x in range(num_nonzero)]
newvals[inds] = thalvals

newimg = nibabel.Nifti1Image(newvals, img.affine, img.header)

nibabel.save(newimg,'rthalatlas.nii.gz')


# Add them to the index/label list
info = pandas.read_csv('atlas-MMP_dseg.tsv', delimiter='\t')
newlabels = [f'thal_{x:05d}' for x in thalvals]

newinfo = pandas.DataFrame(list(zip(thalvals, newlabels)), columns =['index', 'label'])

allinfo = pandas.concat([info, newinfo], axis=0)

allinfo.to_csv('atlas-MMPthal_dseg.tsv', index=False, sep='\t')
