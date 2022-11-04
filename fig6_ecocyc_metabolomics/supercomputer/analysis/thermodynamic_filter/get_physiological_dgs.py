from minedatabase.thermodynamics import Thermodynamics
from minedatabase.pickaxe import Pickaxe
from multiprocessing import Pool, set_start_method
from functools import partial
import pickle
import pandas as pd

from minedatabase.utils import Chunks


def main():
    pk = Pickaxe()
    pk.load_pickled_pickaxe("../../kms_ecoli_metab_100t300r200.pk")
    gen = 0
    rxn_list = []

    rxn_list = list(pk.reactions.keys())
    dg_dict = dict()

    i = 1

    processes = 12
    chunk_size = divmod(len(rxn_list), processes)[0] + 1
    rxn_list_chunks = Chunks(rxn_list, chunk_size=chunk_size, return_list=True)

    get_dg_partial = partial(get_dg, pk)

    print("Starting processes.")
    pool = Pool(processes)
    for res in pool.imap_unordered(get_dg_partial, rxn_list_chunks):
        print(f"Got result {i} of {len(rxn_list)/chunk_size}")
        i += 1
        dg_dict.update(res)

    pickle.dump(dg_dict, open("ecocyc_physiological_dg.pk", "wb"))

    df = pd.DataFrame(
        data=[
            (key, val.value.magnitude, val.error.magnitude)
            for key, val in dg_dict.items()
        ],
        columns=["_id", "value", "error"],
    )
    df.to_csv("thermo_dataframe_physiological.csv", index=False)


def get_dg(pk, rxn_ids):
    print("starting new process")
    thermo = Thermodynamics()
    thermo.load_thermo_from_postgres(
        # URI HERE
    )
    gen_dict = dict()
    for i, rxn_id in enumerate(rxn_ids):
        if i % 100:
            print(i)

        gen_dict[rxn_id] = thermo.physiological_dg_prime_from_rid(rxn_id, pk)

    return gen_dict


if __name__ == "__main__":
    set_start_method("spawn")
    main()
