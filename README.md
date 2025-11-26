# MOT Distributed Data System
**Course:** COMP 410 - Parallel and Distributed Computing

## Project Overview
This project implements a parallelized search and analytics engine for the MOT vehicle dataset (3GB). It utilizes **MPI (Message Passing Interface)** to distribute data processing across multiple nodes (Decomposition) and aggregates results (Reduction) for a central GUI.

## Architecture
*   **Launcher.py:** An administrative GUI to configure cluster IPs and launch the system.
*   **Main_System.py:** The hybrid entry point. Rank 0 becomes the Master (GUI), while Ranks 1-N become headless Workers.
*   **src/mot_engine.py:** Handles Pandas DataFrame operations (Vectorized filtering).
*   **src/mpi_core.py:** Contains the infinite loop logic for Worker nodes.

## How to Run
1.  Place CSV files in `data/`.
2.  Run `python Launcher.py`.
3.  Set number of nodes (e.g., 4) and click "Launch Cluster".

## Features
*   **Cluster Computing:** Configurable via Hostfile editor in Launcher.
*   **Optimization:** Uses Pandas chunking and C-based vectorization.
*   **GUI:** Tkinter-based interface for user queries and graphing. 