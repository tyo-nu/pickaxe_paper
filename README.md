# Pickaxe

This repo contains the code used to generate the data and figures for the Pickaxe paper. Pickaxe is a compound/reaction generation tool that utilizes reaction rules to construct a network of novel compounds and reactions. This tool was used to generate [MINEs for the MINE database](https://academic.oup.com/bioinformatics/article-abstract/38/13/3484/6589885) and the code can be found [here](https://github.com/tyo-nu/MINE-Database).

# Repo Structure
This repo is structured into folders containing code and analysis.

## Figure 3
- Generation code for exponential growth is found in `fig3_gen_exp_growth/run_files/mem_lt300_100r.py`
- Generation code for runtime is found in `fig3_gen_exp_growth/analysis/benchmarks.ipynb`
- Plotting code is found in `fig3_gen_exp_growth/analysis/fig3_plot.ipynb`

## Figure 4
- Generation code is found in `fig4_YMDB_cutoff/`
- Results are stored in a mongo database.
- Analysis code is found in `fig4_gen/analysis/tani_both_analysis.ipynb`

## Figure 5
- Generation code is found in `fig5_sample/C4C8_2k_Conly/runs/`
- Results are stored in mongo databases.
- Analysis code is found in `fig5_sample/C4C8_2k_Conly/analysis/run_production_sampling2k.ipynb`

## Figure 6
- Generation code is found in `fig6_ecocyc_metabolomics/laptop/analysis/ecoli_metabolomics_gen.ipynb`
- Results are stored in a mongo database.
- Analysis code is found in `fig6_ecocyc_metabolomics/laptop/analysis/ecoli_metabolomics_analysis.ipynb`
- The Analysis code can be sped up using `feasibility_first_gen.py`, `feasibility_second_gen_gen2.py`, and `get_physiological_dgs.py`
- The code is also repeated on a supercomputer found in `fig6_ecocyc_metabolomics/supercomputer`

# Software Requirements
The code in this example requires the minedatabase package as well as some additional packages for different filters.

## minedatabase Installation
### Installation via pip

> pip install minedatabase

### Installation from source via conda

> git clone https://github.com/tyo-nu/MINE-Database

then within the MINE-Database folder

> conda env create -f environment.yml
> conda activate minedatabase

## eQuilibrator Installation
The thermodynamics filters require the use of [eQuilibrator](https://equilibrator.readthedocs.io/en/latest/). This can be installed via conda

> conda install -c condaforge equilibrator-api

## DeepRFC Installation
The feasibility filters require the use of DeepRFC, which can be installed by [following the instructions found on their website.](https://bitbucket.org/kaistsystemsbiology/deeprfc/src/master/)

## MongoDB Installation
These examples rely on using a mongo database, either remote or local. To install this database, [download the installer](https://www.mongodb.com/try/download/community) and follow the instructions.

[PyMongo](https://pymongo.readthedocs.io/en/stable/) provides methods to interact with the database via python code.
