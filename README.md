# INFORM-COMPASS-cookbook

## Running the Jupyter Notebook
This cookbook can be run from /glade on Derecho. If you are not already set up, follow the steps below to gain access and configure your environment.

### Obtain access to /glade on Derecho
You will need to run the scripts from Derecho so you can access the ERA5 data stored in /glade. See https://ncar-hpc-docs.readthedocs.io/en/latest/compute-systems/derecho/ for instructions to obtain access.

### Login to Derecho
See https://ncar-hpc-docs.readthedocs.io/en/latest/getting-started/accounts/duo/#logging-in-with-duo for details on authenticating
```bash
> ssh -X <YOUR_USERNAME>@derecho.hpc.ucar.edu
```
* When it asks for ncar-two-factor, enter your CIT password.
* Authenticate with DUO

### Clone this repo to your /glade home directory
```bash
> git clone http://github.com/NCAR/INFORM-COMPASS-cookbook
```

### Set up your environment
Load some standard modules.  For more information, see https://ncar-hpc-docs.readthedocs.io/en/latest/environment-and-software/user-environment/modules/

#### Check which modules are available
```bash
> module av
```
Activate the conda module
```bash
> module load conda
> module av
```
You will now see (L) after conda/latest in the output of the "module av" command indicating that conda has been loaded. **You will have to do this each time you login - it does not persist between login sessions**

#### Set up your Python environment
More info at https://ncar-hpc-docs.readthedocs.io/en/latest/environment-and-software/user-environment/conda/

The environment stored in the environment.yml file is likely already available to you:
```bash
> conda env list
```
To see which env you currently have active
```bash
> conda info
```
Activate the NCAR Python Library (npl) environment.
```bash
> conda activate npl-2024a
```
You should now see (npl-2024a) at the beginning of your command prompt. 

The environment.yml file stored with this code is "npl-2024a".  The "npl" environment always points to the most recent version of the NPL. However, it is recommended that you load a specific version instead if you want to ensure consistent behavior from each installed package.

To create a new environment.yml file (if we ever want to update what is stored with the code:
```bash
> conda env export --no-builds -n npl-<year> > environment.yml
```

### Launch a jupyter environment in your local browser
In order to instantiate a jupyter-lab instance, you will need to access derecho using VNC, FastX (https://fastx.ucar.edu:3300),
 or via jupyterhub.hpc.ucar.edu. Using this last option:
* In the browser on your local maching, enter the URL: ```jupyterhub.hpc.ucar.edu```
* Click the Available NCAR Resources option ```Production```
* Login with your standard Duo credentials and respond to the Duo push notification
* Start a server if you don't already have one running
* Select ```derecho``` and click ```start```
* You will see that you are in your home directory on the left. Navigate to your INFORM-COMPASS-cookbook checkout.
* Click on one of the ipynb files to view that notebook.
