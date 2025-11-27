import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpi4py import MPI

# Ensure we can import from src
sys.path.append(os.getcwd())
from src.mpi_core import worker_loop

# --- MPI SETUP ---
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# --- MASTER GUI CLASS ---
class MasterNodeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"MOT System | Master Node (Rank 0) | {size-1} Workers Connected")
        self.root.geometry("1000x750")
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Tabs
        self.tabs = ttk.Notebook(root)
        self.tab_search = ttk.Frame(self.tabs)
        self.tab_analyze = ttk.Frame(self.tabs)
        self.tabs.add(self.tab_search, text="Distributed Search")
        self.tabs.add(self.tab_analyze, text="Data Analytics")
        self.tabs.pack(expand=1, fill="both")
        
        self.build_search_tab()
        self.build_analyze_tab()

    def build_search_tab(self):
        # Controls
        frame = ttk.LabelFrame(self.tab_search, text="Search Filters")
        frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame, text="Make:").grid(row=0, column=0, padx=5)
        self.ent_make = ttk.Entry(frame); self.ent_make.grid(row=0, column=1)
        
        ttk.Label(frame, text="Model:").grid(row=0, column=2, padx=5)
        self.ent_model = ttk.Entry(frame); self.ent_model.grid(row=0, column=3)
        
        ttk.Label(frame, text="Year:").grid(row=0, column=4, padx=5)
        self.ent_year = ttk.Entry(frame, width=10); self.ent_year.grid(row=0, column=5)
        
        ttk.Button(frame, text="SEARCH CLUSTER", command=self.run_search).grid(row=0, column=6, padx=20)
        
        # Results Table
        cols = ("ID", "Make", "Model", "Date", "Result", "Mileage")
        self.tree = ttk.Treeview(self.tab_search, columns=cols, show="headings")
        for c in cols: self.tree.heading(c, text=c)
        self.tree.pack(expand=True, fill="both", padx=10, pady=5)

    def build_analyze_tab(self):
        # Controls
        frame = ttk.LabelFrame(self.tab_analyze, text="Report Configuration")
        frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame, text="Make:").pack(side="left", padx=5)
        self.an_make = ttk.Entry(frame); self.an_make.pack(side="left")
        
        ttk.Label(frame, text="Model:").pack(side="left", padx=5)
        self.an_model = ttk.Entry(frame); self.an_model.pack(side="left")
        
        self.var_group = tk.StringVar(value="age")
        ttk.Radiobutton(frame, text="By Age", variable=self.var_group, value="age").pack(side="left", padx=10)
        ttk.Radiobutton(frame, text="By Mileage", variable=self.var_group, value="mileage").pack(side="left")
        
        ttk.Button(frame, text="GENERATE GRAPH", command=self.run_analysis).pack(side="left", padx=20)
        
        # Graph Area
        self.graph_frame = tk.Frame(self.tab_analyze, bg="white")
        self.graph_frame.pack(expand=True, fill="both", padx=10, pady=10)

    def run_search(self):
        # 1. Prepare Command
        filters = {
            'make': self.ent_make.get().strip(),
            'model': self.ent_model.get().strip(),
            'year': self.ent_year.get().strip()
        }
        
        # 2. Broadcast to Workers
        comm.bcast({'type': 'SEARCH', 'filters': filters}, root=0)
        
        # 3. Aggregate Results (Reduce)
        results = []
        for i in range(1, size):
            data = comm.recv(source=i)
            if not data.empty:
                results.append(data)
        
        # 4. Display
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        if results:
            final_df = pd.concat(results) # Limit for GUI
            for _, r in final_df.iterrows():
                self.tree.insert("", "end", values=(
                    r['test_id'], r['make'], r['model'], 
                    str(r['test_date'].date()), r['test_result'], r['test_mileage']
                ))
            messagebox.showinfo("Done", f"Cluster returned {len(final_df)} records.")
        else:
            messagebox.showinfo("Result", "No matching records found.")

    def run_analysis(self):
        make = self.an_make.get().strip()
        model = self.an_model.get().strip()
        if not make or not model:
            messagebox.showerror("Error", "Make and Model are required.")
            return

        # 1. Broadcast
        comm.bcast({'type': 'ANALYZE', 'make': make, 'model': model, 'group_by': self.var_group.get()}, root=0)
        
        # 2. Aggregate Stats (Math: Sum of Sums / Sum of Counts)
        total_passed = pd.Series(dtype=float)
        total_count = pd.Series(dtype=float)
        
        for i in range(1, size):
            data = comm.recv(source=i)
            if data is not None:
                total_passed = total_passed.add(data['sum'], fill_value=0)
                total_count = total_count.add(data['count'], fill_value=0)
        
        # 3. Plot
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
            
        if not total_count.empty:
            pass_rate = (total_passed / total_count) * 100
            
            fig = plt.Figure(figsize=(6, 5), dpi=100)
            ax = fig.add_subplot(111)
            pass_rate.sort_index().plot(kind='line', marker='o', ax=ax, color='blue')
            
            ax.set_title(f"Pass Rate for {make} {model}")
            ax.set_ylabel("Pass Percentage (%)")
            ax.set_xlabel("Age (Years)" if self.var_group.get() == 'age' else "Mileage")
            ax.grid(True)
            
            canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            messagebox.showinfo("Info", "No data available for this analysis.")

    def on_close(self):
        if messagebox.askyesno("Exit", "Shutdown entire cluster?"):
            comm.bcast({'type': 'EXIT'}, root=0)
            self.root.destroy()

# --- MAIN ENTRY ---
if __name__ == "__main__":
    if size < 2:
        # Fallback if someone tries to run without mpiexec
        print("Error: Must run via mpiexec with at least 2 processes.")
        sys.exit()

    if rank == 0:
        # Master Node
        root = tk.Tk()
        app = MasterNodeGUI(root)
        root.protocol("WM_DELETE_WINDOW", app.on_close)
        root.mainloop()
    else:
        # Worker Nodes
        worker_loop()