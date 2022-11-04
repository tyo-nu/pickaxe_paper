#!/bin/bash
#SBATCH --account=b1039
#SBATCH --partition=buyin
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=41
#SBATCH --time=100:00:00  
#SBATCH --mem=0G
#SBATCH --job-name=ymdb_lt300_100r_120121_%J_gen2
#SBATCH --output=./outputs/ymdb_lt300_100r_120121_%J_gen2.out
#SBATCH --error=./outputs/ymdb_lt300_100r_120121_%J_gen2.err
#SBATCH --mail-user=kevinshebek2016@u.northwestern.edu
#SBATCH --mail-type=END

module purge all   ## Unload existing modules
python mem_10C.py  ## Run the program
