# File to use postgres instead of the regular local compound cache
# Point of this is to utilize the improved query speed of postgresql over sqlite
from multiprocessing import Queue, Process
from typing import List
import queue
from signal import signal
import sqlalchemy
from equilibrator_cache.compound_cache import CompoundCache
from equilibrator_cache.models.compound import Compound

from equilibrator_assets.local_compound_cache import LocalCompoundCache
import subprocess


class TimeOutException(Exception):
    pass

def alarm_handler(signum, frame):
    raise TimeOutException

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

class psqlCompoundCache(LocalCompoundCache):
    """Use pgsql backend instead of sqlite and add parallel functionality"""
    def __init__(self, psql_uri: str = None):
        super().__init__()
        self.psql_uri = psql_uri

        if psql_uri:
            self.ccache = CompoundCache(sqlalchemy.create_engine(psql_uri))
        
    def load_cache(self, psql_uri: str):
        self.psql_uri = psql_uri
        self.ccache = CompoundCache(sqlalchemy.create_engine(psql_uri))

    def insert_compounds_in_parallel(
        self,
        smiles: List[str],
        n_processes : int = 1,
        chunk_size : int = 100,
        timeout : float = 60
    ):
        # Strictly adds compounds to the DB in parallel.
        # TODO: Make a parallel version with map where order is maintainged?
        # Don't return things now because order is not maintained.
        
        # But return bad compounds if some weren't inserted
        # Bad compounds are returned in the chunk they were attempted to be inserted
        if not self.psql_uri:
            print("Specify a postgresql uri first.")

        # Variables necessary for multiprocess setup
        smiles_in = Queue()
        bad_compounds = Queue()
        processes = []

        # Populate queue that feeds data to processes in chunks
        # get_compounds works better with chunks due to bulk insert into DB
        # Larger chunks are faster, but if any compounds fail then all fail.
        for smi in chunks(smiles, 100):
            smiles_in.put(smi)

        # Spin up the processes, start them, and then wait to close them
        for i in range(n_processes):
            p = Process(
                target=self.get_compounds_in_queue,
                args=(smiles_in, self.psql_uri, bad_compounds, i, timeout)
            )
            processes.append(p)

        for p in processes:
            p.start()

        # Before we can join processes, all queues must be empty*
        # * really actually just have small enough size, but empty is better practice
        # Loop until all processes are dead and get all bad_cpds into a list
        bad_compound_list = []
        while any([p.is_alive() for p in processes]):
            print("I am in here")
            for p in processes:
                p.join(timeout=0.1)

            try:
                bad_compounds.extend(bad_compounds.get_nowait())
            except queue.Empty:
                pass

        # Finally join all processes and close them
        for p in processes:
            p.join()
        
        for p in processes:
            p.close()

        return bad_compound_list

    @staticmethod
    def _insert_compounds_in_queue(smiles_in : Queue, psql_uri : str, bad_compounds : Queue, pid : int = 0, timeout : float = 60):
        """Process to get compounds with the postgresql database.

        This function is meant to live in a process by itself. It receives smiles to make
        through smiles_in Queue and sends any bad compounds to the bad_compounds queue.

        This function loops and reads from smiles_in until the queue is empty and then quits.
        """
        # Timeout function
        signal.signal(signal.SIGALRM, alarm_handler)

        print(f"Creating local cache num: {pid}")
        lcp = LocalCompoundCache()
        lcp.ccache = CompoundCache(sqlalchemy.create_engine(psql_uri))
        print(f"Generated local cache num: {pid}. Creating compounds now.")

        while True:
            try:
                print(f"{pid} attempting to get")
                smiles = smiles_in.get(timeout=2)
                print(f"{pid} got")
            except queue.Empty:
                print(f"{pid} failed")
                break
            else:
                print(f"{pid} getting cpds with timeout {timeout}")
                signal.alarm(timeout)

                try:
                    lcp.get_compounds(smiles, bypass_chemaxon=True, save_empty_compounds=True)
                except TimeOutException:
                    print(f"{pid} has bad cpds!")
                    bad_compounds.put(smiles)
                
                signal.alarm(0)

        return True

    
    def convert_sqlite_to_postgresql(self, local_cache: str, psql_user_uri: str, psql_db_uri, pgloader_fname: str):
        # This requires pgloader to be installed
        # uses eq_compounds by default

        # use my info by default right now
        # TODO: get rid of this data eventually
        psql_user_uri = #URL HERE
        psql_db_uri = #URL HERE
        pgloader_fname = "eQ_sqlite_to_postgres.load"
        # Drop and create new DB
        
        # Drop the database
        try:
            conn = sqlalchemy.create_engine(psql_user_uri).connect()
            conn.execute("commit")
            conn.execute('drop database if exists "eq_compounds"')
            conn.close()
        except:
            print("Unable to drop database, probably due to existing connections. Close all connections and try again.")
            return False
        else:
            conn = sqlalchemy.create_engine(psql_user_uri).connect()
            conn.execute("commit")
            conn.execute('CREATE DATABASE "eq_compounds"')
            conn.close()

            res = subprocess.run(["pgloader", "eQ_sqlite_to_postgres.load"])
            conn = sqlalchemy.create_engine(psql_db_uri).connect()
            conn.execute("commit")
            conn.execute("""
            CREATE SEQUENCE compound_identifiers_id_seq;
            SELECT SETVAL('compound_identifiers_id_seq', (select max(id)+1 from compound_identifiers));
            ALTER TABLE compound_identifiers ALTER COLUMN id SET DEFAULT nextval('compound_identifiers_id_seq'::regclass);

            CREATE SEQUENCE compound_microspecies_id_seq;
            SELECT SETVAL('compound_microspecies_id_seq', (select max(id)+1 from compound_microspecies));
            ALTER TABLE compound_microspecies ALTER COLUMN id SET DEFAULT nextval('compound_microspecies_id_seq'::regclass);

            CREATE SEQUENCE compounds_id_seq;
            SELECT SETVAL('compounds_id_seq', (select max(id)+1 from compounds));
            ALTER TABLE compounds ALTER COLUMN id SET DEFAULT nextval('compounds_id_seq'::regclass);

            CREATE SEQUENCE magnesium_dissociation_constant_id_seq;
            SELECT SETVAL('magnesium_dissociation_constant_id_seq', (select max(id)+1 from magnesium_dissociation_constant));
            ALTER TABLE magnesium_dissociation_constant ALTER COLUMN id SET DEFAULT nextval('magnesium_dissociation_constant_id_seq'::regclass);

            CREATE SEQUENCE registries_id_seq;
            SELECT SETVAL('registries_id_seq', (select max(id)+1 from registries));
            ALTER TABLE registries ALTER COLUMN id SET DEFAULT nextval('registries_id_seq'::regclass);
            """
            )
            conn.close()
            return True



    