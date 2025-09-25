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
