# Running SCAM
Running SCAM on the Derecho supercomputer requires access to CPU core-hours. You will run two files (**after making the changes below**):
* First run create_scamtest.F2000.ne3_ne3_mg37.005.**new**.cold_off.derecho
* Then run create_scamtest.F2000.ne3_ne3_mg37.005.**scm.new**.cold_off.derecho

## See if there is a project/account available for your use
You can find out which projects/accounts are linked to your login via the Systems Accounting Manager webpage

&nbsp;&nbsp;&nbsp;&nbsp;[https://sam.ucar.edu](https://sam.ucar.edu)

or from the command line while logged into Derecho by providing a bogus project to the qinteractive command
```bash
> qinteractive -A P99999999 @derecho
```
The command will return a list of available accounts:
```bash
qsub: Invalid account for CPU usage, available accounts:
Project, Status, Active
Pxxxxxxxx, Normal, True
Pxxxxxxxx, Normal, True
,etc
```
* where xxxxxxxx is the actual project where you have access. If there are no projects available you will need to reach out to whomever in your group/program provides core-hours and request an allocation.

Edit the two SCAM .derecho files and add your project to the create_newcase line

> $CESMDIR/cime/scripts/create_newcase -compset $COMPSET  **--project Pxxxxxxxx** -res $RES -compiler $COMPILER -case $CASEDIR/$CASENAME  -pecount ${PES} --run-unsupported

## Create a scratch directory
You will need to configure a scratch directory where SCAM can write files. Each Derecho user should have a /glade/derecho/scratch directory. Create a scam dir under your scratch dir.
```bash
> ls /glade/derecho/scratch/<YOUR_USERNAME>
> mkdir /glade/derecho/scratch/<YOUR_USERNAME>/scam
```
Now modify the SCAM scripts to point to this directory.  Edit the two SCAM .derecho files and change CASEDIR to point to your scratch scam dir.

> set CASEDIR=/glade/derecho/scratch/<YOUR_USERNAME>/scam

## Modify the scripts to point to the CESM collection directory
These collections are currently stored under John Truesdale's campaign dir so we are using that. **(What do we want to do here long-term?)**  Edit the SCAM .derecho scripts to set this directory.

> set CESMDIR=/glade/campaign/cgd/amp/jet/collections/$CAMDIRNAME

## Run the first file
**Describe what this file does here**
```bash
> ./create_scamtest.F2000.ne3_ne3_mg37.005.new.cold_off.derecho
```

### To check the status of the run:
```bash
more CaseStatus
-or-
qstat -u <YOUR_USERNAME>
```

## Run the second file
**Describe what this file does here**

Once the first run completes, copy the created netCDF file from the scratch scam run dir to just under scratch/<YOUR_USERNAME>. The file path is too long to access it from it's original directory.
```bash
> cp /glade/derecho/scratch/<YOUR_USERNAME>/scam/scamtest.F2000.ne3_ne3_mg37.005.new.cold_off/run/scamtest.F2000.ne3_ne3_mg37.005.new.cold_off.cam.h1i.0001-01-01-00000.nc /glade/derecho/scratch/<YOUR_USERNAME>/.
```

Edit the iopfile dir in create_scamtest.F2000.ne3_ne3_mg37.005.scm.new.cold_off.derecho to point to the shortened location.

> iopfile ='/glade/derecho/scratch/<YOUR_USERNAME>/scamtest.F2000.ne3_ne3_mg37.005.new.cold_off.cam.h1i.0001-01-01-00000.nc'

### Run the file

```bash
> ./create_scamtest.F2000.ne3_ne3_mg37.005.scm.new.cold_off.derecho
```

...Now I just need to know how to look at what I just ran (-:


# Create Nudged IOP forcing using CAM for use with SCAM
This procedure will generating IOP forcing data associated with the dates and area of the SOCRATES field campaign to use with SCAM. The first experiment will provide initial conditions that approximates the state of the atmosphere at daily time intervals throught the period of the SOCRATES field campaign. The ERA5 reanalysis data will be used to nudge the T,U,V and Q fields for the initial CAM run. The second experiment will also be a full 3d cam run which uses the initial condition/restart boundary data along with the CAMIOP and windowing capability of the nudging functionality to generate CAM IOP forcing that can be used with SCAM to rerun the state of any individual column. The third experiment runs the single column version of CAM using the initial condition data along with the IOP forcing to rerun a specific column of the atmosphere during the SOCRATES period. The output of the SCAM run can be compared to the same column of the initial CAM run to see how the model atmosphere evolves (away?) from the nudged (observed) atmospheric state.  Many SCAM runs can be made to analyze the physics processes and modify the parameterizations to help improve the prognosed state.

There are three scripts for making these runs under the SCAM_scripts directory:
* First: CAM6 run to create a ground truth dataset that is nudged to ERA5 reanalysis
  -  SCAM_scripts/create_CAM6_ne30_Global_Nudged_SOCRATES_Jan-Feb_2018
* Second: CAM6 run(s) )to generate CAM IOP data. CAM will nudge to ERA5 reanalysis outside the SOCRATES area
  -  SCAM_scripts/create_CAM6_ne30_Window_Nudged_SOCRATES_CAMIOP_Jan-18-19_RF01
* Third: single column atmosphere (SCAM) run(s) using the generated CAM IOP data.
  -  SCAM_scripts/create_CAM6_ne30_SCAM_RUN

These experiments should be analyzed and improved through several iterations.  Some items for consideration:
* How long a spin up is needed to bring the CAM into a quasi equilibrated state for the SOCRATES start dates?  Our first run started 2 weeks before SOCRATES start. 
* What model variables should be nudged and what nuding parameters work best to achieve a state that is close to the obs but not too far from CAM equilibrium
  -  Exp. 1 and 2 used 6 hour nudging on T,U,V, and Q. Should we just be nudging with T,U, and V?
  -  Exp. 1 is a global nudge to bring the SOCRATES area close to the reanalysis state
  -  Exp. 2 is nudged outside the SOCRATES region using the windowing feature of CAM nudging to allow the physics parameterizations in the SOCRATES area to evolve freely
* How long is the observed state maintained inside the windowed area during the SOCRATES period?
  -  Do we need to use initial nudged IC data before each flight?  How quickly does the model initial state degrade for the various observed weather regimes?
* SCAM only works with boundary data on the dynamics grid.  The physics grid can't be used.  I interpolated Isla's ne30pg3 ERA forcing to the ne30np4 grid but it might be better to have Isla regenerate the forcing data for the ne30np4 grid directly.
* How close is the nudged CAM state to the ERA reanalysis?


