
# Avrillon et al 2024: HDsEMG recordings

BIDS-formatted version of the HDsEMG dataset published in *[Avrillon et al. 2024](https://doi.org/10.7554/eLife.97085.3)*. 
Two experimental sessions consisted of either a series of submaximal (10-80 percent MVC) 
isometric ankle dorsiflexions or isometric knee extensions. EMG signals were recorded from 
either the tibialis anterior (TA) or the vastus lateralis (VL) muscles using four arrays 
of 64 surface electrodes for a total of 256 electrodes.

### Population
16 young individuals volunteered to participate either in the experiment on the 
tibialis anterior (n=8; age: 27 +/- 3) or on the vastus lateralis (n=8; age: 27 +/- 10).

### Electrode placement
Surface EMG signals were recorded from the TA or the VL using 4 two-dimensional arrays of 
64 electrodes (GR04MM1305 for the TA; GR08MM1305 for the VL, 13×5 gold-coated electrodes with 
one electrode absent on a corner; interelectrode distance: 4 and 8 mm, respectively; OT Bioelettronica, Italy). 
The grids were positioned over the muscle bellies to cover the largest surface while staying away from 
the boundaries of the muscle identified by manual palpation. Before placing the electrodes, the 
skin was shaved and cleaned with an abrasive pad and water. A biadhesive foam layer was used to 
hold each array of electrodes onto the skin, and conductive paste filled the cavities of the 
adhesive layers to make skin-electrode contact.

### Tibialis anterior: ankle dorsiflexions
For the session of ankle dorsiflexions, participants sat on a massage table with the 
hips flexed at 45 degree, 0 degree being the hip neutral position, and the knees fully extended. 
The foot of the dominant leg (right in all participants) was fixed onto the pedal of an 
ankle dynamometer (OT Bioelettronica, Turin, Italy) positioned at 30 degree in the plantarflexion 
direction, 0 degree being the foot perpendicular to the shank. The thigh and the foot were 
fixed with inextensible Velcro straps. Force signals were recorded with a load cell 
(CCT Transducer s.a.s, Turin, Italy) connected in-series to the pedal using the same 
acquisition system as for the EMG recordings (EMG-Quattrocento; OT Bioelettronica, Italy).

### Vastus lateralis: knee extensions
For the session of knee extensions, participants sat on an instrumented chair with the hips 
flexed at 85 degree, 0 degree being the hip neutral position, and the knees flexed at 85 degree, 
0 degree being the knees fully extended. The torso and the thighs were fixed to the chair with 
Velcro straps and the tibia were positioned against a rigid resistance connected to force sensors 
(Metitur, Jyvaskyla, Finland). The force signals were recorded using the same acquisition 
system as for the EMG recordings.

### Coordinate systems
All electrode coordinates (reported in mm) have been converted to a common reference 
frame corresponding to the first EMG-array (*space-grid1*). 
The positions of the reference and ground electrodes are reported in a seperate 
coordinate system (*space-lowerLeg*) reported in percent of the lower leg length (knee-to-ankle). 

### Missing data
Contraction intensities 50, 60 and 70 % MVC are missing for subject 15.

### Conversion
The dataset has been converted semi-automatically using the [*MUniverse*](https://github.com/dfarinagroup/muniverse/tree/main) software.
See *dataset_description.json* for further details.

