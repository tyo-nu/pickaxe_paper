import pickle
from minedatabase.pickaxe import Pickaxe
from multiprocessing import Pool

# Uncomment only if using
from minedatabase.filters.feasibility import ReactionFeasibilityFilter, _get_feasibility
from minedatabase.thermodynamics import Thermodynamics

from minedatabase.utils import Chunks
import multiprocessing as mp
from itertools import islice


def get_feasibility(rxn_input):
    def chunks(data, SIZE=10000):
        it = iter(data)
        for _ in range(0, len(data), SIZE):
            yield {k:data[k] for k in islice(it, SIZE)}


    processes = 10
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

    cpd_gen1, cpd_gen2 = 0, 0
    for cpd_id, cpd in pk.compounds.items():
        if cpd["Generation"] == 1:
            cpd_gen1 += 1
        if cpd["Generation"] == 2:
            cpd_gen2 += 1

    feas_filter = ReactionFeasibilityFilter(last_generation_only=True)

    from time import time
    then = time()
    gen = 2
    rxn_list1 = []

    for cpd_id, cpd in pk.compounds.items():
        if "Product_of" in cpd and cpd["Generation"] == gen:
            rxn_list1.extend(cpd["Product_of"])

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

    # print(f"Time took is {time() - then}. For {cpd_gen1} cpds will take {(time() - then)/100*cpd_gen1}s")

    import pickle
    with open("feas_dict_g2.pk", "wb") as f:
        pickle.dump(feasibility_dict1, f)

    with open("feas_results_g2.pk", "wb") as f:
        pickle.dump(feas_results, f)


