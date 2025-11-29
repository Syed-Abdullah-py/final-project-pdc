import pandas as pd

def calculate_pass_rate_by_age(df, make, model):
    # Filter
    subset = df[(df['make'] == make) & (df['model'] == model)].copy()
    if subset.empty:
        return {}

    # Calculate Age: (Test Date - First Use Date) / 365
    subset['age'] = (subset['test_date'] - subset['first_use_date']).dt.days / 365.25
    subset['age'] = subset['age'].fillna(0).astype(int)
    
    # Filter weird ages (e.g. negative or > 100)
    subset = subset[(subset['age'] >= 0) & (subset['age'] < 60)]

    # Grouping
    # Pass = 'P' or 'PRS' (Pass with Rectification)
    subset['is_pass'] = subset['test_result'].isin(['P', 'PRS']).astype(int)
    
    stats = subset.groupby('age')['is_pass'].agg(['count', 'sum'])
    stats['pass_rate'] = (stats['sum'] / stats['count']) * 100
    
    return stats[['count', 'sum']].to_dict('index')

def calculate_pass_rate_by_mileage(df, make, model):
    subset = df[(df['make'] == make) & (df['model'] == model)].copy()
    if subset.empty:
        return {}

    # Bucket mileage by 10,000
    subset['mileage_group'] = (subset['test_mileage'] // 10000) * 10000
    subset = subset[subset['mileage_group'] >= 0]

    subset['is_pass'] = subset['test_result'].isin(['P', 'PRS']).astype(int)
    
    stats = subset.groupby('mileage_group')['is_pass'].agg(['count', 'sum'])
    
    # Return counts and sums for weighted average in coordinator
    return stats[['count', 'sum']].to_dict('index')