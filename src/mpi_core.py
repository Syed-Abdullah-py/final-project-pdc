from mpi4py import MPI
import glob
from src.mot_engine import MOTEngine

def worker_loop():
    """
    The main loop for Worker Nodes (Rank > 0).
    1. Determines file allocation (Decomposition).
    2. Loads data.
    3. Listens for Master commands.
    """
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    
    engine = MOTEngine()
    
    # --- STEP 1: DECOMPOSITION ---
    # Round-Robin file assignment
    all_files = glob.glob("data/*.csv")
    my_files = []
    # Ranks 1 to Size-1 are workers
    for i, f in enumerate(all_files):
        if (i % (size - 1)) + 1 == rank:
            my_files.append(f)
            
    # --- STEP 2: LOAD DATA ---
    # limit_per_file=50000 as suggested in PDF for speed
    engine.load_data(my_files, limit_per_file=50000)
    
    # --- STEP 3: LISTEN FOR COMMANDS ---
    while True:
        # Wait for instruction from Master (Rank 0)
        command = comm.bcast(None, root=0)
        
        if command['type'] == 'EXIT':
            break
            
        elif command['type'] == 'SEARCH':
            # Process Local Search
            result_df = engine.search(command['filters'])
            comm.send(result_df, dest=0)
            
        elif command['type'] == 'ANALYZE':
            # Process Local Analysis
            stats = engine.analyze(command['make'], command['model'], command['group_by'])
            comm.send(stats, dest=0)