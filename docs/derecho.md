---
layout: default # Tells Jekyll to wrap this content with _layouts/default.html
title: Accessing Derecho # Shows up as the text in the browser tab
permalink: /derecho/ # Allows _layouts/default.html to find this page.
---

# Accessing Derecho
The Jupyter Notebooks and SCAM scripts available in this repo can be run from /glade on Derecho. If you are not already set up, follow the steps below to gain access and configure your environment.

## Obtain access to /glade on Derecho
You will need to run the scripts from Derecho so you can access the ERA5 data stored in /glade. See https://ncar-hpc-docs.readthedocs.io/en/latest/compute-systems/derecho/ for instructions to obtain access.

## Login to Derecho
See https://ncar-hpc-docs.readthedocs.io/en/latest/getting-started/accounts/duo/#logging-in-with-duo for details on authenticating
```bash
> ssh -X <YOUR_USERNAME>@derecho.hpc.ucar.edu
```
* When it asks for ncar-two-factor, enter your CIT password.
* Authenticate with DUO

## Create a collections directory to work in
```bash
> mkdir -p $HOME/collections
```

## Clone this repo to your /glade $HOME/collections directory
```bash
> git clone http://github.com/NCAR/INFORM-COMPASS-cookbook
```
or if you already cloned the repo, pull the latest updates
```bash
> cd INFORM-COMPASS-cookbook/
> git pull
```
