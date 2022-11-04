#!/bin/bash
#SBATCH --account=p30041
#SBATCH --partition=short
#SBATCH --nodes=1 
#SBATCH --ntasks-per-node=20
#SBATCH --time=4:00:00  
#SBATCH --mem=40G
#SBATCH --job-name=tani_cutoff_0,8t
#SBATCH --output=./outputs/%j_tani_cutoff_0,8t.out
#SBATCH --error=./outputs/%j_tani_cutoff_0,8t.err
#SBATCH --mail-user=kevinshebek2016@u.northwestern.edu
#SBATCH --mail-type=END

module purge all       ## Unload existing modules
python YMDB_cutoff_0,8t.py  ## Run the program

##!/bin/bash
##SBATCH --account=b1039
##SBATCH --partition=buyin
##SBATCH --nodes=1 
