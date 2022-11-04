# Ecocyc Metabolomics Example
This folder contains an example that was run on a PC to apply rules to the Ecocyc database to attempt to generate matches to an E. coli metabolomics dataset consisting of unannotated peaks.
The following figure highlights the ability of Pickaxe to identify potential compounds, producing the following image. 

![Ecocyc metabolomics example](laptop/figures/fig6_filters_totalPA_scaled.png)

The pickaxe process was run in multiple steps for to track the effect of each filter, each of which took approximately 1.5 to 3 hours to run on 12 cores. It is also possible to run this in one shot.

These examples require [the eQuilibrator local cache to be used](https://equilibrator.readthedocs.io/en/latest/local_cache.html)

## Piecewise run of Pickaxe on PC
This example, contained within the `analysis` folder does the following:

Using `ecoli_metabolomics_data_gen.ipynb` the data for the expansions, feasibility, and thermodynamics are generated. It is worth noting that the feasibility and thermodynamics software are parallelized when used with Pickaxe. The jupyter notebook allows for the generation of both of these data, but due to the parallelization method in Jupyter notebooks (fork) it is better to use the supplied python files to generate feasibility and thermodynamic data.

Finally, `ecoli_metabolomics_analysis.ipynb` details the analysis of this system.

## One-shot run of Pickaxe on PC
This example can be via the `analysis/ecoli_metabolomics_run.py` file to produce the "All" results from the figure. Running at once applies the following:
1. 50 generalized rules
2. An atomic composistion filter for carbon being between 0 and 10.
3. A feasibility filter.
4. A thermodynamics filter requiring ∆G reaction to be less than 50 kJ/mol.

Running this for a second time took approximately 10 hours to run for a 2018, 2.22 GHz 6-Core Intel Core i7 with 16 GB RAM PC.
It must be noted that running this for a first time will take much longer (depending on the PC) due to eQuilibrator having to populate the compounds in its database.


