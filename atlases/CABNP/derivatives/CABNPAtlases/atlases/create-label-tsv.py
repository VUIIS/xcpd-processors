#!/usr/bin/env python3
"""
Write an XCP-D compatible TSV for a CIFTI .dlabel.nii.

Outputs columns:
  index <tab> name

Filters out:
  - index == 0 (background)
  - empty/placeholder names (e.g., "???", "unknown")

Usage:
  python dump_dlabel_to_tsv_filtered.py IN.dlabel.nii [OUT.tsv]

If OUT.tsv is omitted, uses IN with ".dlabel.nii" replaced by ".tsv".
"""

import sys
import numpy as np
import nibabel as nb
import pandas as pd


def usage(exit_code=2):
    prog = sys.argv[0] if sys.argv else "dump_dlabel_to_tsv_filtered.py"
    print(f"Usage: {prog} IN.dlabel.nii [OUT.tsv]", file=sys.stderr)
    sys.exit(exit_code)


if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
    usage(0)

in_dlabel = sys.argv[1]
out_tsv = sys.argv[2] if len(sys.argv) > 2 else in_dlabel.replace(".dlabel.nii", ".tsv")

img = nb.load(in_dlabel)
ax = img.header.get_axis(0)  # label axis for dlabel

labels = getattr(ax, "label", None) or getattr(ax, "labels", None)
if labels is None:
    raise RuntimeError("Could not locate label table on axis 0.")

# Unwrap nibabel object-array wrapper if present
while isinstance(labels, np.ndarray) and labels.dtype == object and labels.shape == (1,):
    labels = labels.item()

if not hasattr(labels, "items"):
    labels = dict(labels)


def label_name(v):
    if isinstance(v, (tuple, list)) and len(v) >= 1:
        return str(v[0])
    return str(getattr(v, "label", None) or getattr(v, "name", None) or v)


bad_names = {"", "???", "unknown", "Unknown", "UNLABELED", "unlabeled", "background", "Background"}

rows = []
for k, v in labels.items():
    k = int(k)
    name = label_name(v).strip()
    if k == 0:
        continue
    if name in bad_names:
        continue
    rows.append({"index": k, "name": name})

rows.sort(key=lambda r: r["index"])

df = pd.DataFrame(rows, columns=["index", "name"])
df.to_csv(out_tsv, sep="\t", index=False)
print(f"Wrote {out_tsv} ({len(df)} labels; dropped background/unknown entries)")