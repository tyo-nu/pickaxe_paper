#!/bin/bash
#SBATCH --account=p30041
#SBATCH --partition=short
#SBATCH --nodes=1 
#SBATCH --ntasks-per-node=20
#SBATCH --time=2:00:00
#SBATCH --mem=15G
#SBATCH --job-name=ecoli_metfilter50r_100t300gmol
#SBATCH --output=outputs/%j_ecoli_metfilter50r_100t300gmol.out
#SBATCH --error=outputs/%j_ecoli_metfilter50r_100t300gmol.err
#SBATCH --mail-user=kevinshebek2016@u.northwestern.edu
#SBATCH --mail-type=END

module purge all       ## Unload existing modules
python ecoli_metfilter.py # Run the program