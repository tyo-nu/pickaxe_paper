#!/bin/bash
#SBATCH --account=b1039
#SBATCH --partition=buyin
#SBATCH --nodes=1 
#SBATCH --ntasks-per-node=40
#SBATCH --time=90:00:00  
#SBATCH --mem=0G
#SBATCH --job-name=tani_cutoff2g_0,2t
#SBATCH --output=./outputs/%j_tani_cutoff2g_0,2t.out
#SBATCH --error=./outputs/%j_tani_cutoff2g_0,2t.err
#SBATCH --mail-user=kevinshebek2016@u.northwestern.edu
#SBATCH --mail-type=END

module purge all       ## Unload existing modules
python YMDB_cutoff_0,2t.py  ## Run the program

##SBATCH --account=b1039
##SBATCH --partition=buyin
##SBATCH --nodes=1 

##SBATCH --account=p30041
##SBATCH --partition=short
