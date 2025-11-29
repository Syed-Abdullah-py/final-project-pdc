import sys
from mpi4py import MPI
from src.worker import run_worker
from src.coordinator import run_coordinator

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    if rank == 0:
        print("Starting Coordinator (GUI)...")
        run_coordinator()
    else:
        print(f"Starting Worker {rank}...")
        run_worker()

if __name__ == "__main__":
    main()