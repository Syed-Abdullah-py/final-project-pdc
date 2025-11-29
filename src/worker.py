from mpi4py import MPI
from .loader import load_local_data
from .config import TAG_search, TAG_ANALYZE, TAG_EXIT
from .analytics import calculate_pass_rate_by_age, calculate_pass_rate_by_mileage

def run_worker():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    
    # 1. Load Data
    df = load_local_data(rank, size - 1) # size-1 because rank 0 is master

    while True:
        # Wait for command from Coordinator
        command = comm.recv(source=0)
        
        tag = command['tag']
        payload = command['payload']

        if tag == TAG_EXIT:
            break

        elif tag == TAG_search:
            # payload: {'make': 'BMW', 'model': '3 SERIES', 'year': 2014, ...}
            temp_df = df.copy()
            
            if payload.get('make'):
                temp_df = temp_df[temp_df['make'] == payload['make']]
            if payload.get('model'):
                temp_df = temp_df[temp_df['model'] == payload['model']]
            if payload.get('year'):
                # Extract year from first_use_date
                temp_df = temp_df[temp_df['first_use_date'].dt.year == int(payload['year'])]
            
            # Range Logic (Mileage)
            min_m = payload.get('min_mileage')
            max_m = payload.get('max_mileage')
            
            if min_m is not None:
                temp_df = temp_df[temp_df['test_mileage'] >= int(min_m)]
            if max_m is not None:
                temp_df = temp_df[temp_df['test_mileage'] <= int(max_m)]

            # Select top 100 to avoid clogging network, send as list of dicts
            result_data = temp_df.head(100).to_dict('records')
            comm.send(result_data, dest=0)

        elif tag == TAG_ANALYZE:
            # payload: {'type': 'age'|'mileage', 'make': ..., 'model': ...}
            if payload['type'] == 'age':
                res = calculate_pass_rate_by_age(df, payload['make'], payload['model'])
            else:
                res = calculate_pass_rate_by_mileage(df, payload['make'], payload['model'])
            
            comm.send(res, dest=0)