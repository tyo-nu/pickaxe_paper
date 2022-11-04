import numpy as np
from tqdm import tqdm

from pymongo import MongoClient
client = MongoClient()

import pandas as pd

from multiprocessing import Pool
from rdkit import Chem, DataStructs
 
tqdm.pandas()
# cores = cpu_count() #Number of CPU cores on your system
# partitions = cores #Define as many partitions as you want
db_list = ["YMDB_2ksampleC_T0", "YMDB_2ksampleC_T3", "YMDB_2ksampleC_T6"]
db = db_list[2]
target_smiles = [target["SMILES"] for target in client[db].target_compounds.find()]
def parallelize(data, func, cores):
    data_split = np.array_split(data, cores)
    pool = Pool(cores)
    data = pd.concat(pool.map(func, data_split))
    pool.close()
    pool.join()
    return data

def func_help(data):
    print(data.columns)
    data["max_similarity"] = data["SMILES"].progress_map(get_max_similarity)
    print('done')
    return data

def get_max_similarity(smi):
    mol = mfs(smi)

    max_similarity = 0
    mol_fp = Chem.RDKFingerprint(mol)

    for target_smi in target_smiles:
        target_mol = mfs(target_smi)
        target_fp = Chem.RDKFingerprint(target_mol)
        similarity = DataStructs.TanimotoSimilarity(mol_fp, target_fp)
        if max_similarity < similarity:
            max_similarity = similarity
 

        if max_similarity == 1:
            break
    
    return max_similarity

def mfs(smi):
    return Chem.MolFromSmiles(smi)

if __name__ == "__main__":
    compound_smiles = [compound["SMILES"] for compound in client[db].compounds.find()]

    similarity_df = pd.DataFrame(compound_smiles, columns=["SMILES"])

    similarity_df = parallelize(similarity_df, func_help, 10)

    print("done")