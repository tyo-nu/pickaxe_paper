import signal
import subprocess
import time

import sqlalchemy
from minedatabase.pickaxe import Pickaxe

print("starting eQ imports")
import pickle
import queue
from multiprocessing import Process, Queue, process, set_start_method

from equilibrator_assets.local_compound_cache import LocalCompoundCache
from equilibrator_cache import Compound
from equilibrator_cache.compound_cache import CompoundCache
from equilibrator_assets.chemaxon import get_chemaxon_status
from pymongo import MongoClient

from psql_compound_cache import psqlCompoundCache

print("ChemAxon License:", get_chemaxon_status())

URI_EQ = # URI HERE


class TimeOutException(Exception):
    pass


def alarm_handler(signum, frame):
    raise TimeOutException


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


# def reset_eq_compounds():
#     # Drop and create new DB

#     try:
#         conn = sqlalchemy.create_engine(uri_kbot).connect()
#         conn.execute("commit")
#         conn.execute('drop database if exists "eq_compounds"')
#         conn.close()
#     except:
#         print(
#             "Unable to drop database, probably due to existing connections. Close all connections and try again."
#         )
#         return False
#     else:
#         conn = sqlalchemy.create_engine(uri_kbot).connect()
#         conn.execute("commit")
#         conn.execute('CREATE DATABASE "eq_compounds"')
#         conn.close()

#         res = subprocess.run(["pgloader", "eQ_sqlite_to_postgres.load"])
#         conn = sqlalchemy.create_engine(uri_eq).connect()
#         conn.execute("commit")
#         conn.execute(
#             """
#         CREATE SEQUENCE compound_identifiers_id_seq;
#         SELECT SETVAL('compound_identifiers_id_seq', (select max(id)+1 from compound_identifiers));
#         ALTER TABLE compound_identifiers ALTER COLUMN id SET DEFAULT nextval('compound_identifiers_id_seq'::regclass);

#         CREATE SEQUENCE compound_microspecies_id_seq;
#         SELECT SETVAL('compound_microspecies_id_seq', (select max(id)+1 from compound_microspecies));
#         ALTER TABLE compound_microspecies ALTER COLUMN id SET DEFAULT nextval('compound_microspecies_id_seq'::regclass);

#         CREATE SEQUENCE compounds_id_seq;
#         SELECT SETVAL('compounds_id_seq', (select max(id)+1 from compounds));
#         ALTER TABLE compounds ALTER COLUMN id SET DEFAULT nextval('compounds_id_seq'::regclass);

#         CREATE SEQUENCE magnesium_dissociation_constant_id_seq;
#         SELECT SETVAL('magnesium_dissociation_constant_id_seq', (select max(id)+1 from magnesium_dissociation_constant));
#         ALTER TABLE magnesium_dissociation_constant ALTER COLUMN id SET DEFAULT nextval('magnesium_dissociation_constant_id_seq'::regclass);

#         CREATE SEQUENCE registries_id_seq;
#         SELECT SETVAL('registries_id_seq', (select max(id)+1 from registries));
#         ALTER TABLE registries ALTER COLUMN id SET DEFAULT nextval('registries_id_seq'::regclass);
#         """
#         )
#         conn.close()
#         return True


def get_compound_pg(smi_queue, cpd_queue):
    print("Loading")
    lcp = LocalCompoundCache()
    lcp.ccache = CompoundCache(sqlalchemy.create_engine(URI_EQ))

    while True:
        try:
            smi = smi_queue.get(timeout=2)
        except:
            break
        else:
            cpd = lcp.get_compounds(
                smi, bypass_chemaxon=True, save_empty_compounds=True
            )
            cpd_queue.put(cpd)

    lcp.ccache.session.close()
    del lcp
    print("exiting")
    return True


def get_compound_batch(smiles):
    print("Loading")
    lcp = LocalCompoundCache()
    lcp.ccache = CompoundCache(sqlalchemy.create_engine(URI_EQ))

    cpds = lcp.get_compounds(smiles, bypass_chemaxon=True, save_empty_compounds=True)

    lcp.ccache.session.close()
    del lcp.ccache
    return cpds


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


# --------------- Single Process Stuff
def test_single_process(smiles):
    """Test a single process eQuilibrator (i.e. default) with postgresql DB"""
    print("Connecting to postresql DB.")
    lcp = LocalCompoundCache()
    lcp.ccache = CompoundCache(sqlalchemy.create_engine(URI_EQ))

    compounds = []
    then = time.time()
    for smi in smiles:
        compounds.append(
            lcp.get_compounds(smi, bypass_chemaxon=True, save_empty_compounds=True)
        )

    now = time.time()

    print(f"Single process took {now - then}s.")
    return compounds


# --------------- Queue Stuff
def get_compounds_in_queue(smiles_in, compounds_out, bad_compounds, pid=0, timeout=360):
    "starting par in queue"
    signal.signal(signal.SIGALRM, alarm_handler)

    then = time.time()
    print(f"Connecting {pid} to postgresql DB.")
    
    lcp = LocalCompoundCache()
    i = 0
    if lcp.read_only:
        del lcp
        print(f"Exiting and terminating process due to bad license: {pid}")
        return True

    lcp.ccache = CompoundCache(sqlalchemy.create_engine(URI_EQ))
    print(f"Started this ({pid}) lcp in {time.time() - then}s\nGetting Compounds")

    then = time.time()
    while True:
        try:
            smiles = smiles_in.get(timeout=2)
            print(smiles)
            print(f"{pid} succesfully got smiles.")
        except queue.Empty:
            print(f"{pid} failed to get smiles, terminating.")
            break
        else:
            print(f"{pid} getting cpds with timeout {timeout}")
            signal.alarm(timeout)

            try:
                compounds = lcp.get_compounds(
                    smiles, bypass_chemaxon=True, save_empty_compounds=True
                )
                if type(compounds) == Compound:
                    compounds = [compounds]

                compounds_out.put([compounds])

                print(f"{pid} succesfully got compounds.")
            except TimeOutException:
                print(f"{pid} timed out getting compounds, adding to bad compounds.")
                bad_compounds.put(smiles)
            except BaseException as e:
                print(
                    f"Another error happened, adding to bad compounds. Error was:\n{e}"
                )
                bad_compounds.put(smiles)

            signal.alarm(0)

    lcp.ccache.session.close()
    del lcp
    print(f"Exiting and terminating process: {pid}")
    return True


def test_single_queue(smiles, n_processes):
    """Test using single compounds in queue"""
    smiles_in = Queue()
    compounds_out = Queue()

    processes = []

    for smi in smiles:
        smiles_in.put(smi)

    then_imp = time.time()

    for i in range(n_processes):
        p = Process(target=get_compounds_in_queue, args=(smiles_in, compounds_out))
        processes.append(p)

    for p in processes:
        p.start()

    then_after_imp = time.time()

    for p in processes:
        p.join()

    now = time.time()

    print(
        f"Ran get_compounds on {len(smiles)} compounds with {n_processes} took:\nWith imports: {now-then_imp}\nWithout imports: {now-then_after_imp}"
    )


def test_chunk_queue(smiles, n_processes, chunk_size=1):
    """Test using chunked compounds in queue"""
    smiles_in = Queue()
    compounds_out = Queue()
    bad_compounds = Queue()

    processes = []
    timeout = 360

    for smi in chunks(smiles, 1):
        smiles_in.put(smi)

    then_imp = time.time()

    for i in range(n_processes):
        p = Process(
            target=get_compounds_in_queue,
            args=(smiles_in, compounds_out, bad_compounds, i, timeout),
        )
        processes.append(p)

    for p in processes:
        p.start()

    then_after_imp = time.time()
    cpds = []
    bad_cpds = []
    i = 0
    while any([p.is_alive() for p in processes]):
        for p in processes:
            p.join(timeout=0.1)

        try:
            cpds.extend(compounds_out.get_nowait())
        except queue.Empty:
            pass

        try:
            bad_cpds.append(bad_compounds.get_nowait())
        except queue.Empty:
            pass

    print("joined")
    for p in processes:
        p.join()

    now = time.time()

    print(
        f"Ran get_compounds on {len(smiles)} compounds with {n_processes} took:\nWith imports: {now-then_imp}\nWithout imports: {now-then_after_imp}"
    )
    return bad_cpds


def test_psql_cache(smiles, n_processes):
    pcc = psqlCompoundCache()
    pcc.load_cache()

    then = time.time()
    bad_cpds = pcc.insert_compounds_in_parallel(
        smiles, n_processes, chunk_size=20, timeout=120
    )
    print(f"psql_cache took: {time.time() - then}")


def main():
    # pcc = psqlCompoundCache()
    print("Loading SMILES")
    pk = Pickaxe()
    pk.load_pickled_pickaxe("../../kms_ecoli_metab_100t300r200.pk")

    smiles = [cpd["SMILES"] for cpd in pk.compounds.values()]
    # smiles = smiles[:100]
    print(f"Total SMILES: {len(smiles)}")

    print("-" * 30)
    print("\nBeginning parallel eQuilibrator generation.")

    # can be: single
    # par_get is queues and get_compounds with N instances
    # parg_et_chunk
    test_type = "par_get_chunk"
    reset_db = False
    n_processes = 12

    chunk_size = 1

    # if reset_db:
    #     print('reseting')
    #     reset = reset_eq_compounds()
    #     if reset:
    #         print('done resetting')
    #     else:
    #         print("failed to reset")
    #         return False

    if test_type == "single":
        compounds = test_single_process(smiles)
    elif test_type == "par_get":
        compounds = test_single_queue(smiles, n_processes)
    elif test_type == "par_get_chunk":
        compounds = test_chunk_queue(smiles, n_processes, chunk_size)
    elif test_type == "psql_cache":
        test_psql_cache(smiles, n_processes)

    print(f"\n{'-'*50}\nEnded parallel.")
    if compounds:
        pickle.dump(compounds, open("bad_compounds.pk", "wb"))
        print(f"{len(compounds)} chunks contained bad compounds")
    else:
        print("No bad compounds")


if __name__ == "__main__":
    set_start_method("spawn")
    main()
