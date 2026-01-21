---
layout: default # Tells Jekyll to wrap this content with _layouts/default.html
title: Scam Tips # Shows up as the text in the browser tab
permalink: /scam_tips/ # Allows _layouts/default.html to find this page.
---

## Scam Tips

## To check the status of the run:
```tcsh
> cd $SCRATCH/cases/<your_case_name>
> more CaseStatus
-or-
> qstat -u <YOUR_USERNAME>
```
[qstat documentation](https://ncar-hpc-docs.readthedocs.io/en/latest/pbs/?h=qstat#qstat)

## To delete a run
```tcsh
qdel #######
```
where ###### is the Job ID from qstat. Before you can run again, you may need to clean up the run dir:
```tcsh
> cd $SCRATCH/cases/<your_case_name>
> ./case.build --clean
> ./case.build --clean-all
```

