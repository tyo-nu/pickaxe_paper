#!/bin/bash
#SBATCH --account=b1039
#SBATCH --partition=buyin
#SBATCH --nodes=1 
#SBATCH --ntasks-per-node=40
#SBATCH --time=24:00:00  
#SBATCH --mem=0G
#SBATCH --job-name=tani_sampleC2k_T0
#SBATCH --output=./outputs/%j_tani_sampleC2k_T0.out
#SBATCH --error=./outputs/%j_tani_sampleC2k_T0.err
#SBATCH --mail-user=kevinshebek2016@u.northwestern.edu
#SBATCH --mail-type=END

module purge all       ## Unload existing modules
python YMDB_sampleC2k_T0.py  ## Run the program

## SBATCH --account=b1039
## SBATCH --partition=buyin
## SBATCH --nodes=1 


##SBATCH --account=p30041
##SBATCH --partition=short
##SBATCH --nodes=1 