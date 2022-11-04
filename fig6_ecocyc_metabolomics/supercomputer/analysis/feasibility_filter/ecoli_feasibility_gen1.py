import pickle
from minedatabase.pickaxe import Pickaxe
from multiprocessing import Pool
from time import time

from minedatabase.filters.feasibility import ReactionFeasibilityFilter, _get_feasibility

import multiprocessing as mp
from itertools import islice

# Function to generate feasibility in parallel
def get_feasibility(rxn_input):
    def chunks(data, SIZE=10000):
        it = iter(data)
        for _ in range(0, len(data), SIZE):
            yield {k: data[k] for k in islice(it, SIZE)}

    processes = 8
    print("starting pools")
    pool = Pool(processes)
    print("finishing pools")

    chunk_size = divmod(len(rxn_input), processes)[0] + 1
    rxn_chunks = chunks(rxn_input, chunk_size)

    results = dict()
    i = 0
    for res in pool.imap_unordered(_get_feasibility, rxn_chunks):
        print("res", i)
        i += 1
        results.update(res)

    return results


if __name__ == "__main__":
    mp.set_start_method("spawn")
    pk = Pickaxe()
    pk.load_pickled_pickaxe("../../kms_ecoli_metab_100t300r200.pk")
    feas_filter = ReactionFeasibilityFilter()

    then = time()
    gen = 1
    rxn_list1 = []

    total_cpds = 0
    for cpd_id, cpd in pk.compounds.items():
        if "Product_of" in cpd and cpd["Generation"] == gen:
            rxn_list1.extend(cpd["Product_of"])
            total_cpds += 1

    test_rxns = list(set(rxn_list1))

    rxn_input, failed1 = feas_filter._get_inputs(test_rxns, pk)
    feas_results = get_feasibility(rxn_input)
    

    feasibility_dict1 = dict()
    for rxn_id, feas_result in feas_results.items():
        rxn_id = rxn_id.split("_")[0]
        # Set to true if any are feasible, set to false if doesn't
        if feas_result[2] == "feasible":
            feasibility_dict1[rxn_id] = True
        elif rxn_id not in feasibility_dict1:
            feasibility_dict1[rxn_id] = False

    for rxn_id in failed1:
        if rxn_id not in feasibility_dict1:
            feasibility_dict1[rxn_id] = False

    # print(f"Time took for 300 is {time() - then}. For {total_cpds} cpds will take {(time() - then)/300*total_cpds}s")

    # import pickle

    with open("feas_dict_g1_.pk", "wb") as f:
        pickle.dump(feasibility_dict1, f)

    with open("feas_results_g1_.pk", "wb") as f:
        pickle.dump(feas_results, f)
