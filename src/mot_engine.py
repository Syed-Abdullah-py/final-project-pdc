import pandas as pd
import os

class MOTEngine:
    """
    The Data Handling Unit.
    Uses Pandas DataFrames as the efficient Data Structure.
    """
    def __init__(self):
        self.data = pd.DataFrame()
        # Optimization: Pre-defining types to save memory
        self.columns = [
            'test_id', 'vehicle_id', 'test_date', 'test_class_id', 
            'test_type', 'test_result', 'test_mileage', 'postcode_area', 
            'make', 'model', 'colour', 'fuel_type', 
            'cylinder_capacity', 'first_use_date'
        ]

    def load_data(self, file_paths, limit_per_file=50000):
        """
        Loads data from assigned CSVs.
        Uses chunks to handle large files (Optimization).
        """
        dfs = []
        for f_path in file_paths:
            if not os.path.exists(f_path):
                continue
            
            try:
                # Reading in chunks prevents Memory Overflow
                # quotechar='"' handles the "BMW, 3 Series" comma issue
                chunk_reader = pd.read_csv(
                    f_path, names=self.columns, header=0, 
                    chunksize=5000, quotechar='"', escapechar='\\', 
                    on_bad_lines='skip', low_memory=False
                )

                rows_loaded = 0
                for chunk in chunk_reader:
                    # Optimization: Drop rows with missing keys immediately
                    chunk.dropna(subset=['make', 'model', 'test_result'], inplace=True)
                    
                    # Optimization: Keep only necessary columns for the assignment
                    keep_cols = ['test_id', 'make', 'model', 'test_date', 
                                 'test_result', 'test_mileage', 'first_use_date']
                    # Filter columns that exist in the chunk
                    existing_cols = [c for c in keep_cols if c in chunk.columns]
                    dfs.append(chunk[existing_cols])
                    
                    rows_loaded += len(chunk)
                    if limit_per_file and rows_loaded >= limit_per_file:
                        break
            except Exception as e:
                print(f"[Error] Could not read {f_path}: {e}")

        if dfs:
            self.data = pd.concat(dfs, ignore_index=True)
            # Post-processing: Convert Dates and Calculate Age
            self.data['test_date'] = pd.to_datetime(self.data['test_date'], errors='coerce')
            self.data['first_use_date'] = pd.to_datetime(self.data['first_use_date'], errors='coerce')
            self.data['vehicle_age'] = (self.data['test_date'] - self.data['first_use_date']).dt.days / 365.25
        else:
            self.data = pd.DataFrame(columns=['test_id', 'make', 'model'])

    def search(self, filters):
        """ Returns top 100 matching records """
        if self.data.empty: return pd.DataFrame()
        
        df = self.data
        
        # Vectorized Filtering (O(1) approach using C-bindings)
        if filters.get('make'):
            df = df[df['make'].str.contains(filters['make'], case=False, na=False)]
        if filters.get('model'):
            df = df[df['model'].str.contains(filters['model'], case=False, na=False)]
        if filters.get('year'):
            df = df[df['first_use_date'].dt.year == int(filters['year'])]
        if filters.get('min_miles'):
            df = df[df['test_mileage'] >= float(filters['min_miles'])]
        if filters.get('max_miles'):
            df = df[df['test_mileage'] <= float(filters['max_miles'])]
            
        return df.head(100)

    def analyze(self, make, model, group_by):
        """ Returns aggregated stats (Sum/Count) for reduction """
        if self.data.empty: return None
        
        subset = self.data[
            (self.data['make'].str.upper() == make.upper()) & 
            (self.data['model'].str.upper() == model.upper())
        ].copy()
        
        if subset.empty: return None

        # 1 = Pass, 0 = Fail
        subset['is_pass'] = subset['test_result'].isin(['P', 'PRS']).astype(int)
        
        if group_by == 'age':
            subset['group'] = subset['vehicle_age'].fillna(0).astype(int)
        else: # mileage
            subset['group'] = (subset['test_mileage'] // 10000) * 10000
            
        # Return Sum and Count so Master can calculate true weighted average
        return subset.groupby('group')['is_pass'].agg(['sum', 'count'])