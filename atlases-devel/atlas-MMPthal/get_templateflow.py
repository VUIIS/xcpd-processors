#!/usr/bin/env python
#
# https://www.templateflow.org/usage/client/

from templateflow import api as tflow
path = tflow.get('MNI152NLin6Asym', desc=None, resolution=2,
    suffix='T1w', extension='nii.gz')
print(path)
