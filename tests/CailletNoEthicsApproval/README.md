
# Caillet et al 2023: HDsEMG recordings

BIDS-formatted version of the HDsEMG dataset published in *[Caillet et al. 2023](https://doi.org/10.1523/ENEURO.0064-23.2023)*. 

### Population
Six healthy male subjects (age: 26 +/- 4 years; height: 174 +/- 7 cm; weight: 66 +/- 15 kg).

### Protocol description
Each participant performed two trapezoidal contractions at 30 percent and 50 percent MVC, 
with 120 s of rest in between, consisting of linear ramps up and down performed at 
5 percent per second and a plateau maintained for 20 and 15 s at 30 percent and 
50 percent MVC, respectively. The order of the contractions was randomized.

### Electrode placement
First, the skin was shaved, abrased and cleansed with 70 percent ethyl alcohol.
Next, four grids (64 channels) were carefully positioned side-to-side with a 4-mm distance between the 
electrodes at the edges of adjacent grids. The 256 electrodes were centered on the 
muscle belly (right tibialis anterior) and laid within the muscle perimeter identified 
through palpation. Two bands damped with water were placed around the ankle as 
ground (R2) and reference (R1) electrodes. 

### Set-up description
The participant sat on a massage table with the hips flexed at 30 degrees, 0 degrees being 
the hip neutral position, and their knees fully extended. We fixed the foot of 
the dominant leg (right in all participants) onto the pedal of a commercial dynamometer (OT Bioelettronica) 
positioned at 30 degrees in the plantarflexion direction, 0 degrees being the foot 
perpendicular to the shank. The thigh was fixed to the massage table with an 
inextensible 3-cm-wide Velcro strap. The foot was fixed to the pedal with inextensible 
straps positioned around the proximal phalanx, metatarsal, and cuneiform. Force signals 
were recorded with a load cell (CCT Transducer s.a.s.) connected in-series to the pedal 
using the same acquisition system as for the HD-EMG recordings. The dynamometer was 
positioned according to the participant's lower limb length and secured to the massage table 
to avoid any motion during the contractions. 

### Missing data
There is no 50 % MVC ramp-and-hold contraction for the second subject.

### Coordinate systems
All electrode coordinates (reported in mm) have been converted to a common reference 
frame corresponding to the first EMG-array (*space-grid1*). 
The positions of the reference and ground electrodes are reported in a separate 
coordinate system (*space-lowerLeg*) reported as a percentage of the lower leg length. 

### Conversion
The dataset has been converted semi-automatically using the [*MUniverse*](https://github.com/dfarinagroup/muniverse/tree/main) software.
See *dataset_description.json* for further details.

