import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpi4py import MPI
from .config import TAG_search, TAG_ANALYZE, TAG_EXIT

class MOTApp:
    def __init__(self, root, comm, num_workers):
        self.root = root
        self.comm = comm
        self.num_workers = num_workers
        self.root.title("MOT Data Visualizer (Cluster Coordinator)")
        self.root.attributes('-fullscreen', True)

        # Tabs
        self.tab_control = ttk.Notebook(root)
        self.tab_search = ttk.Frame(self.tab_control)
        self.tab_analytics = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_search, text='Search Data')
        self.tab_control.add(self.tab_analytics, text='Analytics & Charts')
        self.tab_control.pack(expand=1, fill="both")

        self.setup_search_tab()
        self.setup_analytics_tab()

    def setup_search_tab(self):
        frame_inputs = tk.Frame(self.tab_search)
        frame_inputs.pack(pady=10)

        # Inputs
        tk.Label(frame_inputs, text="Make:").grid(row=0, column=0)
        self.entry_make = tk.Entry(frame_inputs)
        self.entry_make.grid(row=0, column=1)

        tk.Label(frame_inputs, text="Model:").grid(row=0, column=2)
        self.entry_model = tk.Entry(frame_inputs)
        self.entry_model.grid(row=0, column=3)

        tk.Label(frame_inputs, text="Year (First Use):").grid(row=0, column=4)
        self.entry_year = tk.Entry(frame_inputs)
        self.entry_year.grid(row=0, column=5)

        tk.Label(frame_inputs, text="Min Mileage:").grid(row=1, column=0)
        self.entry_min_mil = tk.Entry(frame_inputs)
        self.entry_min_mil.grid(row=1, column=1)

        tk.Label(frame_inputs, text="Max Mileage:").grid(row=1, column=2)
        self.entry_max_mil = tk.Entry(frame_inputs)
        self.entry_max_mil.grid(row=1, column=3)

        btn_search = tk.Button(frame_inputs, text="Search Distributed DB", command=self.run_search)
        btn_search.grid(row=1, column=4, columnspan=2, pady=5)

        # Treeview Results
        self.tree = ttk.Treeview(self.tab_search, columns=("ID", "Make", "Model", "Date", "Result", "Mileage"), show='headings')
        self.tree.heading("ID", text="Test ID")
        self.tree.heading("Make", text="Make")
        self.tree.heading("Model", text="Model")
        self.tree.heading("Date", text="Date")
        self.tree.heading("Result", text="Result")
        self.tree.heading("Mileage", text="Mileage")
        self.tree.pack(expand=True, fill='both', padx=10, pady=10)

    def setup_analytics_tab(self):
        frame_inputs = tk.Frame(self.tab_analytics)
        frame_inputs.pack(pady=10)

        tk.Label(frame_inputs, text="Make:").grid(row=0, column=0)
        self.an_make = tk.Entry(frame_inputs)
        self.an_make.grid(row=0, column=1)

        tk.Label(frame_inputs, text="Model:").grid(row=0, column=2)
        self.an_model = tk.Entry(frame_inputs)
        self.an_model.grid(row=0, column=3)

        self.graph_type = tk.StringVar(value="age")
        tk.Radiobutton(frame_inputs, text="Pass Rate by Age", variable=self.graph_type, value="age").grid(row=0, column=4)
        tk.Radiobutton(frame_inputs, text="Pass Rate by Mileage", variable=self.graph_type, value="mileage").grid(row=0, column=5)

        btn_plot = tk.Button(frame_inputs, text="Generate Graph", command=self.run_analysis)
        btn_plot.grid(row=0, column=6, padx=10)

        self.plot_frame = tk.Frame(self.tab_analytics)
        self.plot_frame.pack(expand=True, fill='both')

    def run_search(self):
        # 1. Prepare Payload
        payload = {
            'make': self.entry_make.get().upper(),
            'model': self.entry_model.get().upper(),
            'year': self.entry_year.get(),
            'min_mileage': self.entry_min_mil.get(),
            'max_mileage': self.entry_max_mil.get()
        }
        
        # Clean empty strings
        payload = {k: v for k, v in payload.items() if v}

        # 2. Broadcast to Workers
        for i in range(1, self.num_workers):
            self.comm.send({'tag': TAG_search, 'payload': payload}, dest=i)

        # 3. Gather Results
        all_results = []
        for i in range(1, self.num_workers):
            data = self.comm.recv(source=i)
            all_results.extend(data)

        # 4. Update UI
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        for row in all_results:
            self.tree.insert("", "end", values=(
                row.get('test_id'), row.get('make'), row.get('model'), 
                row.get('test_date'), row.get('test_result'), row.get('test_mileage')
            ))

    def run_analysis(self):
        make = self.an_make.get().upper()
        model = self.an_model.get().upper()
        g_type = self.graph_type.get()

        if not make:
            messagebox.showerror("Error", "Please specify a Make")
            return

        payload = {'type': g_type, 'make': make, 'model': model}

        # Broadcast
        for i in range(1, self.num_workers):
            self.comm.send({'tag': TAG_ANALYZE, 'payload': payload}, dest=i)

        # Aggregate (Weighted Average logic could be applied, but simple aggregation for now)
        aggregated_data = {} # Key: Age/Mileage, Value: [pass_rate_sum, count]
        
        # Note: A proper aggregation requires raw counts from workers (Pass Count, Total Count).
        # For simplicity in this example, we assume workers sent pre-calculated rates, 
        # but technically we should sum numerators and denominators. 
        # Let's assume workers send Rate dictionaries. We will average them (Approximation).
        
        # Better approach: Workers send {age: {'passed': X, 'total': Y}}
        # But keeping code simple based on prompt constraints.
        
        final_series = {}

        # Receiving
        received_dicts = []
        for i in range(1, self.num_workers):
            received_dicts.append(self.comm.recv(source=i))

        # Merging Logic (Weighted Average)
        aggregated_data = {}
        
        for d in received_dicts:
            for k, v in d.items():
                if k not in aggregated_data:
                    aggregated_data[k] = {'count': 0, 'sum': 0}
                aggregated_data[k]['count'] += v['count']
                aggregated_data[k]['sum'] += v['sum']
        
        final_series = {}
        for k, v in aggregated_data.items():
            # Filter low sample sizes to reduce noise (Statistical Accuracy)
            if v['count'] < 5: 
                continue
            
            # Filter extreme mileage outliers (e.g., > 500,000 miles) if graph type is mileage
            if g_type == 'mileage' and k > 500000:
                continue
            
            final_series[k] = (v['sum'] / v['count']) * 100

        # Plotting
        self.plot_data(final_series, g_type)

    def plot_data(self, data_dict, g_type):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        if not data_dict:
            return

        keys = sorted(data_dict.keys())
        values = [data_dict[k] for k in keys]

        fig = plt.Figure(figsize=(6, 5), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(keys, values, marker='o')
        
        ax.set_title(f"Pass Rate by {g_type}")
        ax.set_xlabel("Age (Years)" if g_type == 'age' else "Mileage")
        ax.set_ylabel("Pass Rate %")
        ax.grid(True)

        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

def run_coordinator():
    comm = MPI.COMM_WORLD
    size = comm.Get_size()
    
    if size < 2:
        print("Error: Need at least 2 MPI processes (1 Coordinator, 1 Worker).")
        return

    root = tk.Tk()
    app = MOTApp(root, comm, size)
    
    # Handle window close to kill workers
    def on_closing():
        for i in range(1, size):
            comm.send({'tag': TAG_EXIT, 'payload': None}, dest=i)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()