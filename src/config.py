import os

# Limits to save time (as per PDF suggestion)
# Set to None to load ALL data (Production), or 50000 for Development
ROWS_PER_FILE = 50000 

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# MPI Tags
TAG_search = 1
TAG_ANALYZE = 2
TAG_EXIT = 0