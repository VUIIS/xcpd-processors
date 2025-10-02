Schaeffer cortical atlases from here:
https://github.com/ThomasYeoLab/CBIG/tree/master/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal/Parcellations/MNI

Tian subcortical atlas from here:
https://www.nitrc.org/frs/download.php/13364/Tian2020MSA_v1.4.zip


Tian has two resolutions (1mm, 2mm), and two atlas spaces:
  Unmarked:   MNI152NLin6Asym
  2009cAsym:  MNI152NLin2009cAsym

Schaeffer atlases have two resolutions (1mm, 2mm), and are in a single atlas space called FSLMNI152. 
Looks like that is either MNI152NLin6Sym or MNI152NLin6ASym 
(https://bids-specification.readthedocs.io/en/latest/appendices/coordinate-systems.html). 
According to the readme the underlying template image is at 
https://github.com/ThomasYeoLab/CBIG/blob/master/data/templates/volume/FSL_MNI152_FS4.5.0/mri/orig/001.mgz. 
That is the standard MNI that comes with FSL. It is quite clearly asymmetric compared to the ICBM at 
https://www.bic.mni.mcgill.ca/ServicesAtlases/ICBM152NLin6, 
so I conclude the Schaeffer atlases are in the MNI152NLin6Asym space.

