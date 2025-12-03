import pandas as pd
import glob
import os
from .config import DATA_DIR, ROWS_PER_FILE

def load_local_data(rank, total_workers):
    """
    Loads a partition of data based on the worker rank.
    Reads files in chunks to allow progress updates every 1000 rows.
    """
    all_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    
    if not all_files:
        print(f"[Worker {rank}] No CSV files found in {DATA_DIR}")
        return pd.DataFrame()

    # Distribute files among workers (Round Robin)
    my_files = [f for i, f in enumerate(all_files) if i % total_workers == (rank - 1)]
    
    data_frames = []
    
    cols = [
        "test_id", "vehicle_id", "test_date", "test_class_id", 
        "test_type", "test_result", "test_mileage", "postcode_area", 
        "make", "model", "colour", "fuel_type", 
        "cylinder_capacity", "first_use_date"
    ]

    print(f"[Worker {rank}] Assigned {len(my_files)} files.")

    for f in my_files:
        filename = os.path.basename(f)
        print(f"[Worker {rank}] START processing file: {filename}")
        
        file_chunks = []
        rows_loaded_this_file = 0
        
        try:
            # We use chunksize=1000 to satisfy the requirement of printing every 1000 rows
            with pd.read_csv(
                f, 
                names=cols, 
                header=0, 
                chunksize=1000,  # Read in chunks of 1000
                quotechar='"', 
                escapechar='\\',
                low_memory=False
            ) as reader:
                
                for chunk in reader:
                    # --- CLEANING (Done per chunk to save memory/time) ---
                    
                    # String cleaning
                    chunk['make'] = chunk['make'].str.upper().str.strip()
                    chunk['model'] = chunk['model'].str.upper().str.strip()
                    chunk['test_result'] = chunk['test_result'].str.upper().str.strip()
                    
                    # Date cleaning
                    chunk['test_date'] = pd.to_datetime(chunk['test_date'], errors='coerce')
                    chunk['first_use_date'] = pd.to_datetime(chunk['first_use_date'], errors='coerce')
                    
                    # Numeric cleaning
                    chunk['test_mileage'] = pd.to_numeric(chunk['test_mileage'], errors='coerce')
                    
                    # Append cleaned chunk
                    file_chunks.append(chunk)
                    
                    # Update counters
                    rows_loaded_this_file += len(chunk)
                    
                    # Since chunksize is 1000, this loop runs every 1000 rows.
                    print(f"[Worker {rank}] Imported {rows_loaded_this_file} rows from {filename}...")

                    # Check against the global limit (if set in config)
                    if ROWS_PER_FILE is not None and rows_loaded_this_file >= ROWS_PER_FILE:
                        print(f"[Worker {rank}] Reached limit of {ROWS_PER_FILE} rows for {filename}.")
                        break
            
            # Combine all chunks for this specific file
            if file_chunks:
                file_df = pd.concat(file_chunks, ignore_index=True)
                data_frames.append(file_df)
                
            print(f"[Worker {rank}] END processing file: {filename}. Total rows: {rows_loaded_this_file}")

        except Exception as e:
            print(f"[Worker {rank}] Error loading {filename}: {e}")

    if data_frames:
        full_df = pd.concat(data_frames, ignore_index=True)
        print(f"[Worker {rank}] All files loaded. Total Dataset Size: {len(full_df)} rows.")
        return full_df
    else:
        return pd.DataFrame(columns=cols)