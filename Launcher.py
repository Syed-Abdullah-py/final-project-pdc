import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import os
import platform  # Added to detect Mac vs Windows

class ClusterLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("MOT Cluster Manager (Launcher)")
        self.root.geometry("600x450")
        
        # Determine OS for correct MPI flags
        self.os_type = platform.system()
        
        # Config Area
        lbl = ttk.Label(root, text=f"HPC Cluster Configuration ({self.os_type} Detected)", font=("Arial", 14, "bold"))
        lbl.pack(pady=10)
        
        frm_cfg = ttk.Frame(root)
        frm_cfg.pack(pady=5)
        
        ttk.Label(frm_cfg, text="Number of Processes (Nodes):").pack(side="left")
        self.ent_n = ttk.Entry(frm_cfg, width=5)
        self.ent_n.insert(0, "4")
        self.ent_n.pack(side="left", padx=5)
        
        # Hostfile Editor
        ttk.Label(root, text="Hostfile (IP Configuration):").pack(anchor="w", padx=20)
        self.txt_hosts = scrolledtext.ScrolledText(root, height=8, width=60)
        self.txt_hosts.pack(pady=5)
        
        self.load_defaults()
        
        # Buttons
        btn_frm = ttk.Frame(root)
        btn_frm.pack(pady=20)
        
        ttk.Button(btn_frm, text="Save Config", command=self.save_config).pack(side="left", padx=10)
        ttk.Button(btn_frm, text="LAUNCH CLUSTER", command=self.launch).pack(side="left", padx=10)
        
        self.lbl_status = ttk.Label(root, text="Status: Idle", foreground="gray")
        self.lbl_status.pack(side="bottom", pady=5)

    def load_defaults(self):
        path = "config/cluster_hosts.txt"
        if os.path.exists(path):
            with open(path, "r") as f:
                self.txt_hosts.insert("1.0", f.read())
        else:
            # Default content
            self.txt_hosts.insert("1.0", "localhost slots=4")

    def save_config(self):
        os.makedirs("config", exist_ok=True)
        with open("config/cluster_hosts.txt", "w") as f:
            f.write(self.txt_hosts.get("1.0", tk.END).strip())
        messagebox.showinfo("Saved", "Cluster configuration updated.")

    def launch(self):
        self.save_config()
        n_proc = self.ent_n.get()
        hostfile = "config/cluster_hosts.txt"
        script = "Main_System.py"
        
        # --- HARVARD LEVEL FIX: OS DETECTION ---
        # Windows (MS-MPI) uses -f
        # Mac/Linux (OpenMPI) uses --hostfile and often requires --oversubscribe
        
        if self.os_type == "Windows":
            cmd = ["mpiexec", "-n", n_proc, "python", script]
        else:
            # For Mac/Linux (OpenMPI)
            # --oversubscribe allows spawning more processes than physical cores (useful for testing)
            cmd = ["mpiexec", "-n", n_proc, "--hostfile", hostfile, "--oversubscribe", "python", script]
        
        self.lbl_status.config(text=f"Launching {n_proc} nodes on {self.os_type}...", foreground="blue")
        print(f"Executing command: {' '.join(cmd)}") # Print to terminal for debugging
        
        try:
            # We use Popen to let the launcher stay open
            subprocess.Popen(cmd)
            self.lbl_status.config(text="Cluster Running. Check for new Window.", foreground="green")
        except FileNotFoundError:
            messagebox.showerror("Error", "MPI Executable not found.\nIs OpenMPI (Mac) or MS-MPI (Windows) installed?")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ClusterLauncher(root)
    root.mainloop()