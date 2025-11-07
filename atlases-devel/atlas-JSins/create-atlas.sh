#!/usr/bin/env bash

# Verify no overlap
fslmaths \
	InsulaCluster_K3_L-dAI \
	-add InsulaCluster_K3_L-PI \
	-add InsulaCluster_K3_L-vAI \
	-add InsulaCluster_K3_R-dAI \
	-add InsulaCluster_K3_R-PI \
	-add InsulaCluster_K3_R-vAI \
	sum
fslstats sum -R


# ROI names and indices (matching below image creation)
cat << EOF > atlas-JSins_dseg.tsv
index	label
1	L-dAI
2	L-PI
3	L-vAI
4	R-dAI
5	R-PI
6	R-vAI
EOF

# Individual ROI masks
fslmaths InsulaCluster_K3_L-dAI -bin -mul 1 L-dAI
fslmaths InsulaCluster_K3_L-PI  -bin -mul 2 L-PI
fslmaths InsulaCluster_K3_L-vAI -bin -mul 3 L-vAI
fslmaths InsulaCluster_K3_R-dAI -bin -mul 4 R-dAI
fslmaths InsulaCluster_K3_R-PI  -bin -mul 5 R-PI
fslmaths InsulaCluster_K3_R-vAI -bin -mul 6 R-vAI

# Combine
fslmaths L-dAI -add L-PI -add L-vAI -add R-dAI -add R-PI -add R-vAI \
	atlas-JSins_space-MNI152NLin6Asym_dseg

