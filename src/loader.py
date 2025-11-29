import pandas as pd
import glob
import os
from .config import DATA_DIR, ROWS_PER_FILE

def load_local_data(rank, total_workers):
    """
    Loads a partition of data based on the worker rank.
    If there are 4 files and 2 workers:
    Worker 1 takes files [0, 2], Worker 2 takes files [1, 3] (Round Robin).
    """
    all_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    
    if not all_files:
        return pd.DataFrame()

    my_files = [f for i, f in enumerate(all_files) if i % total_workers == (rank - 1)]
    
    data_frames = []
    
    cols = [
        "test_id", "vehicle_id", "test_date", "test_class_id", 
        "test_type", "test_result", "test_mileage", "postcode_area", 
        "make", "model", "colour", "fuel_type", 
        "cylinder_capacity", "first_use_date"
    ]

    print(f"[Worker {rank}] Loading {len(my_files)} files...")

    for f in my_files:
        try:
            # Handling escaped quotes and commas as per PDF warning
            df = pd.read_csv(
                f, 
                names=cols, 
                header=0, 
                nrows=ROWS_PER_FILE, 
                quotechar='"', 
                escapechar='\\',
                low_memory=False
            )
            
            # Basic Cleaning
            df['make'] = df['make'].str.upper().str.strip()
            df['model'] = df['model'].str.upper().str.strip()
            df['test_result'] = df['test_result'].str.upper().str.strip()
            
            # Convert dates
            df['test_date'] = pd.to_datetime(df['test_date'], errors='coerce')
            df['first_use_date'] = pd.to_datetime(df['first_use_date'], errors='coerce')
            
            df['test_mileage'] = pd.to_numeric(df['test_mileage'], errors='coerce')
            df.dropna(subset=['test_mileage'], inplace=True)
            df['test_mileage'] = pd.to_numeric(df['test_mileage'], errors='coerce')

            data_frames.append(df)
        except Exception as e:
            print(f"[Worker {rank}] Error loading {f}: {e}")

    if data_frames:
        full_df = pd.concat(data_frames, ignore_index=True)
        print(f"[Worker {rank}] Ready. Loaded {len(full_df)} rows.")
        return full_df
    else:
        return pd.DataFrame(columns=cols)