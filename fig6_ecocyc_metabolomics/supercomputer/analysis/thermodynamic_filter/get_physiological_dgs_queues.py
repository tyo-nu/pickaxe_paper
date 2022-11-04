import signal
import time
from minedatabase.pickaxe import Pickaxe


import pickle
import queue
from multiprocessing import Process, Queue, process, set_start_method
from minedatabase.thermodynamics import Thermodynamics
import pandas as pd
from minedatabase.utils import Chunks

URI_EQ = # URI HERE


class TimeOutException(Exception):
    pass


def alarm_handler(signum, frame):
    raise TimeOutException


# --------------- Queue Stuff
def get_reactions_in_queue(reaction_in, reactions_out, pid=0, timeout=360):
    print(f"Start process {pid}, loading pk")
    pk = Pickaxe()
    pk.load_pickled_pickaxe("../../kms_ecoli_metab_100t300r200.pk")
    signal.signal(signal.SIGALRM, alarm_handler)

    then = time.time()
    print(f"Spinning up Thermo Analysis for {pid}.")

    thermo = Thermodynamics()
    thermo.load_thermo_from_postgres(
        #URI HERE
    )
    i = 0
    if thermo.lc.read_only:
        del thermo
        print(f"Exiting and terminating process due to license issues: {pid}")
        return None

    print(f"Started process ({pid}) lcp in {time.time() - then}s\nGetting Reactions")

    dg_dict = dict()
    then = time.time()
    while True:
        try:
            reaction_ids = reaction_in.get(timeout=2)
            # print(smiles)
            print(f"{pid} succesfully got reactions.")
        except queue.Empty:
            print(f"Terminating process {pid}: failed to get reaction ids.")
            break
        else:
            # print(f"Calculating reaction for process {pid} with timeout {timeout}")
            signal.alarm(timeout)
            for reaction_id in reaction_ids:
                try:
                    dg_dict[reaction_id] = thermo.physiological_dg_prime_from_rid(reaction_id, pk)
                    # print(dg_phys, reaction_id)
                    # print(f"{pid} succesfully got physiological dG.")
                except TimeOutException:
                    print(f"{pid} timed out getting reaction {reaction_id}.")
                    dg_dict[reaction_id] = None
                    # bad_reactions.put(reaction_id)
                except BaseException as e:
                    print(
                        f"Another error happened, adding to bad compounds. Error was:\n{e}"
                    )
                    # bad_reactions.put(reaction_id)

                signal.alarm(0)

            reactions_out.put(dg_dict)

    # Close postgres connection
    thermo.lc.ccache.session.close()
    del thermo
    print(f"Exiting and terminating process: {pid}")
    return True


def get_reactions_parallel(reaction_ids, n_processes):
    """Test using chunked compounds in queue"""
    # Define Queues
    reaction_in = Queue()
    reactions_out = Queue()

    # Parameters for processes
    processes = []
    timeout = 30
    
    def chunks(lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i : i + n]
    i = 0

    chunk_size = int(len(reaction_ids)/n_processes) + 1
    for reaction_id in chunks(reaction_ids, chunk_size):
        i += 1
        reaction_in.put(reaction_id)
    
    then_imp = time.time()

    for i in range(n_processes):
        p = Process(
            target=get_reactions_in_queue,
            args=(reaction_in, reactions_out, i, timeout),
        )
        processes.append(p)

    for p in processes:
        p.start()

    then_after_imp = time.time()
    dg_dict = dict()

    print("starting calcs")
    while any([p.is_alive() for p in processes]):
        for p in processes:
            p.join(timeout=0.1)

        try:
            for reaction_id, dg_val in  reactions_out.get_nowait().items():
                dg_dict[reaction_id] = dg_val
        except queue.Empty:
            pass

    print("Joining Processes")
    for p in processes:
        p.join()

    now = time.time()

    print(
        f"Calculated dg phys for {len(reaction_ids)} with {n_processes} took:\n\tWith imports: {now-then_imp}\n\tWithout imports: {now-then_after_imp}"
    )

    return dg_dict


def main():
    # pcc = psqlCompoundCache()
    print("Loading SMILES")
    pk = Pickaxe()
    pk.load_pickled_pickaxe("../../kms_ecoli_metab_100t300r200.pk")

    reactions = list(pk.reactions)

    print(f"Total Reactions: {len(reactions)}")

    print("-" * 30)
    print("\nBeginning physiological dG calculations.")

    n_processes = 8

    reactions = get_reactions_parallel(reactions, n_processes)

    print(f"\n{'-'*50}\nEnded parallel.")

    print("Dumping to pickle and csv.")
    pickle.dump(reactions, open("physiological_dgs.pk", "wb"))
    df = pd.DataFrame(
        data=[
            (key, val.value.magnitude, val.error.magnitude)
            for key, val in reactions.items()
        ],
        columns=["_id", "value", "error"],
    )
    df.to_csv("thermo_dataframe_physiological.csv", index=False)


if __name__ == "__main__":
    set_start_method("spawn")
    main()
