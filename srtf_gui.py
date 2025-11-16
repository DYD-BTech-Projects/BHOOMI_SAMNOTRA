# ==============================
# srtf_gui.py
# FRONTEND GUI for SRTF Scheduling
# Features:
# - Animated and scrollable Gantt chart
# - Dropdown for individual process stats
# - Automatic average time calculation
# - Modern, clean UI using Tkinter
# ==============================

import tkinter as tk                # GUI toolkit for Python
from tkinter import ttk, messagebox # For styled widgets and popup messages
import math                         # Used for calculations
from srtf_logic import srtf_scheduling  # Import backend scheduling logic

# -------------------------------------------------------
# Generate a unique, soft color for each process ID (PID)
# -------------------------------------------------------
def color_for_pid(pid):
    h = abs(hash(pid)) % (0xFFFFFF)
    r = (h >> 16) & 0xFF
    g = (h >> 8) & 0xFF
    b = h & 0xFF
    # Make colors brighter for better visibility
    r = int((r + 180) / 2) if r < 100 else r
    g = int((g + 180) / 2) if g < 100 else g
    b = int((b + 180) / 2) if b < 100 else b
    return "#{:02x}{:02x}{:02x}".format(r, g, b)

# -------------------------------------------------------
# Combine consecutive same PID entries into one segment
# Used for creating Gantt chart blocks
# -------------------------------------------------------
def build_segments(gantt):
    if not gantt:
        return []
    segs = []
    cur = gantt[0]
    start = 0
    length = 1
    for i in range(1, len(gantt)):
        if gantt[i] == cur:
            length += 1
        else:
            segs.append((cur, start, length))
            cur = gantt[i]
            start = i
            length = 1
    segs.append((cur, start, length))
    return segs

# -------------------------------------------------------
# Main GUI Application Class
# -------------------------------------------------------
class SRTFApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SRTF CPU Scheduling Visualizer")
        self.root.geometry("1250x750")
        self.root.configure(bg="#f6f8fb")
        self.processes = []      # Stores added processes
        self.proc_results = []   # Stores computed results
        self._build_ui()         # Build the complete UI

    # ---------------------------------------------------
    # UI Design Section — creates all GUI components
    # ---------------------------------------------------
    def _build_ui(self):
        # ---------- Header ----------
        header = tk.Frame(self.root, bg="#0f4c81", height=90)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="SRTF CPU Scheduling Simulator", bg="#0f4c81", fg="white",
                 font=("Segoe UI", 20, "bold")).pack(pady=(10,0))
        tk.Label(header, text="Shortest Remaining Time First — table-style Gantt, animated",
                 bg="#0f4c81", fg="#d6e9fb", font=("Segoe UI", 10)).pack()

        # ---------- Main area ----------
        main = tk.Frame(self.root, bg="#f6f8fb")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        # ---------- Left panel (Inputs) ----------
        left = tk.Frame(main, bg="white", bd=1, relief="flat")
        left.place(relx=0.01, rely=0.02, relwidth=0.28, relheight=0.94)
        tk.Label(left, text="Add Process", bg="white", font=("Segoe UI", 14, "bold")).pack(pady=(12,6))

        # --- Input form for process data ---
        form = tk.Frame(left, bg="white")
        form.pack(padx=12, anchor="w")
        tk.Label(form, text="Process ID", bg="white").grid(row=0, column=0, sticky="w", pady=4)
        tk.Label(form, text="Arrival", bg="white").grid(row=1, column=0, sticky="w", pady=4)
        tk.Label(form, text="Burst", bg="white").grid(row=2, column=0, sticky="w", pady=4)

        # --- Input boxes for process data ---
        self.pid_entry = tk.Entry(form, width=8)
        self.at_entry = tk.Entry(form, width=8)
        self.bt_entry = tk.Entry(form, width=8)
        self.pid_entry.grid(row=0, column=1, padx=8, pady=4)
        self.at_entry.grid(row=1, column=1, padx=8, pady=4)
        self.bt_entry.grid(row=2, column=1, padx=8, pady=4)

        # --- Buttons to add or clear data ---
        tk.Button(left, text="Add Process", bg="#2b6cff", fg="white", font=("Segoe UI", 10, "bold"),
                  command=self.add_process).pack(pady=(8,4), ipadx=6)
        tk.Button(left, text="Clear All", bg="#ff6b6b", fg="white", font=("Segoe UI", 9, "bold"),
                  command=self.clear_all).pack(pady=(0,8), ipadx=6)

        # --- Table to show added processes ---
        tk.Label(left, text="Processes", bg="white", font=("Segoe UI", 12, "bold")).pack(pady=(6,4))
        cols = ("PID", "Arrival", "Burst")
        self.proc_tree = ttk.Treeview(left, columns=cols, show="headings", height=12)
        for c in cols:
            self.proc_tree.heading(c, text=c)
            self.proc_tree.column(c, width=100, anchor="center")
        self.proc_tree.pack(padx=10, pady=6, fill="both", expand=True)

        # --- Button to start calculation ---
        tk.Button(left, text="Calculate & Visualize", bg="#00b894", fg="white",
                  font=("Segoe UI", 10, "bold"), command=self.on_calculate).pack(pady=8, ipadx=6)

        # ---------- Right panel (Results & Gantt) ----------
        right = tk.Frame(main, bg="white", bd=0)
        right.place(relx=0.31, rely=0.02, relwidth=0.68, relheight=0.94)
        tk.Label(right, text="Visualization", bg="white", font=("Segoe UI", 14, "bold")).pack(pady=(8,6), anchor="w")

        # --- Table for results ---
        stats_cols = ("PID","Arrival","Burst","CT","TAT","WT")
        self.stats_tree = ttk.Treeview(right, columns=stats_cols, show="headings", height=5)
        for c in stats_cols:
            self.stats_tree.heading(c, text=c)
            self.stats_tree.column(c, width=90, anchor="center")
        self.stats_tree.pack(fill="x", padx=12)

        # --- Gantt Chart area ---
        tk.Label(right, text="Gantt Chart (table-style)", bg="white", font=("Segoe UI", 11)).pack(pady=(10,2), anchor="w", padx=12)
        gantt_container = tk.Frame(right, bg="white")
        gantt_container.pack(fill="both", expand=True, padx=12, pady=(4,12))
        self.gantt_canvas = tk.Canvas(gantt_container, bg="#f8fbff", height=220)
        self.h_scroll = tk.Scrollbar(gantt_container, orient="horizontal", command=self.gantt_canvas.xview)
        self.gantt_canvas.configure(xscrollcommand=self.h_scroll.set)
        self.h_scroll.pack(side="bottom", fill="x")
        self.gantt_canvas.pack(side="left", fill="both", expand=True)
        self.gantt_inner = tk.Frame(self.gantt_canvas, bg="#f8fbff")
        self.gantt_window = self.gantt_canvas.create_window((0,0), window=self.gantt_inner, anchor="nw")

        # --- Legend + Dropdown for process stats ---
        self.legend_frame = tk.Frame(right, bg="white")
        self.legend_frame.pack(fill="x", padx=12, pady=(6,0))

        dropdown_frame = tk.Frame(right, bg="white")
        dropdown_frame.pack(fill="x", padx=12, pady=(6,0))
        tk.Label(dropdown_frame, text="Check individual process:", bg="white", font=("Segoe UI", 10, "bold")).pack(side="left")

        # --- Dropdown menu for processes ---
        self.selected_pid = tk.StringVar()
        self.process_dropdown = ttk.Combobox(dropdown_frame, textvariable=self.selected_pid, state="readonly", width=10)
        self.process_dropdown.pack(side="left", padx=10)
        self.process_dropdown.bind("<<ComboboxSelected>>", self.show_selected_process_stats)

        # --- Display for selected process result ---
        self.single_proc_label = tk.Label(right, text="", bg="white", font=("Segoe UI", 10))
        self.single_proc_label.pack(padx=12, pady=(4,0), anchor="w")

        # --- Footer (average stats) ---
        self.footer_label = tk.Label(right, text="", bg="white", font=("Segoe UI", 11, "bold"))
        self.footer_label.pack(padx=12, pady=6, anchor="w")

        # --- Configure canvas scroll ---
        self.gantt_inner.bind("<Configure>", lambda e: self.gantt_canvas.configure(scrollregion=self.gantt_canvas.bbox("all")))

    # ---------------------------------------------------
    # Function to add process to table and list
    # ---------------------------------------------------
    def add_process(self):
        pid = self.pid_entry.get().strip()
        at = self.at_entry.get().strip()
        bt = self.bt_entry.get().strip()

        # Validation checks
        if not pid:
            messagebox.showerror("Input Error", "Please enter Process ID (e.g. P1).")
            return
        try:
            at_i = int(at)
            bt_i = int(bt)
        except:
            messagebox.showerror("Input Error", "Arrival and Burst must be integers.")
            return

        # Auto-format PID
        if pid.isdigit():
            pid = f"P{pid}"

        # Add process to list and table
        self.processes.append({"pid": pid, "arrival": at_i, "burst": bt_i})
        self.proc_tree.insert("", "end", values=(pid, at_i, bt_i))

        # Clear input boxes
        self.pid_entry.delete(0, "end")
        self.at_entry.delete(0, "end")
        self.bt_entry.delete(0, "end")

    # ---------------------------------------------------
    # Clear all inputs and visualizations
    # ---------------------------------------------------
    def clear_all(self):
        self.processes.clear()
        for tree in [self.proc_tree, self.stats_tree]:
            for r in tree.get_children():
                tree.delete(r)
        self.gantt_canvas.delete("all")
        for w in self.legend_frame.winfo_children():
            w.destroy()
        self.footer_label.config(text="")
        self.single_proc_label.config(text="")
        self.process_dropdown["values"] = []

    # ---------------------------------------------------
    # Handle the main calculation and visualization
    # ---------------------------------------------------
    def on_calculate(self):
        if not self.processes:
            messagebox.showwarning("No data", "Please add at least one process.")
            return

        # Get results from backend SRTF logic
        procs, avg_wt, avg_tat, gantt = srtf_scheduling(self.processes.copy())
        self.proc_results = procs

        # Display results in table
        for r in self.stats_tree.get_children():
            self.stats_tree.delete(r)
        for p in procs:
            self.stats_tree.insert("", "end", values=(p["pid"], p["arrival"], p["burst"], p["ct"], p["tat"], p["wt"]))

        # Show average times
        self.footer_label.config(text=f"Average Waiting Time: {avg_wt:.2f}    |    Average Turnaround Time: {avg_tat:.2f}")

        # Populate dropdown menu
        self.process_dropdown["values"] = [p["pid"] for p in procs]
        self.process_dropdown.set("")

        # Build and display animated Gantt chart
        segments = build_segments(gantt)
        self._draw_gantt_with_animation(segments)

    # ---------------------------------------------------
    # Draw Gantt chart with animation
    # ---------------------------------------------------
    def _draw_gantt_with_animation(self, segments):
        self.gantt_canvas.delete("all")
        for w in self.legend_frame.winfo_children():
            w.destroy()

        total_units = sum(length for (_, _, length) in segments)
        if total_units == 0:
            return

        # Adjust cell width according to number of units
        self.root.update_idletasks()
        canvas_width = max(self.gantt_canvas.winfo_width(), 600)
        padding = 20
        desired_cell_w = 60
        max_fit_cell_w = (canvas_width - padding*2) / max(total_units, 1)
        cell_w = min(desired_cell_w, max(18, max_fit_cell_w))
        total_width = int(padding*2 + math.ceil(total_units * cell_w))
        self.gantt_canvas.configure(scrollregion=(0,0, total_width, 300))

        # Assign colors to processes
        color_map = {"Idle": "#d6dde0"}
        for pid, _, _ in segments:
            if pid != "Idle" and pid not in color_map:
                color_map[pid] = color_for_pid(pid)

        # Prepare animation
        start_x, y, h = padding, 40, 56
        per_unit_list = []
        for pid, start, length in segments:
            per_unit_list.extend([pid]*length)

        self._anim_state = {
            "per_unit": per_unit_list, "cell_w": cell_w, "start_x": start_x,
            "y": y, "h": h, "color_map": color_map, "index": 0
        }

        # Outline the chart box
        self.gantt_canvas.create_rectangle(start_x-2, y-2, start_x + total_units*cell_w +2, y + h +2, outline="#999", width=1)

        # Display legend for colors
        for pid, color in color_map.items():
            tk.Label(self.legend_frame, text="  ", bg=color, bd=1, relief="solid").pack(side="left", padx=(6,2))
            tk.Label(self.legend_frame, text=pid, bg="white", font=("Segoe UI", 9)).pack(side="left", padx=(0,8))

        # Start animation
        self._animate_step()

    # ---------------------------------------------------
    # Animate step-by-step drawing of Gantt chart
    # ---------------------------------------------------
    def _animate_step(self):
        st = self._anim_state
        per_unit = st["per_unit"]
        idx = st["index"]
        if idx >= len(per_unit):
            self._draw_time_markers(per_unit, st["start_x"], st["y"], st["cell_w"])
            return

        pid = per_unit[idx]
        x0 = st["start_x"] + idx * st["cell_w"]
        x1 = x0 + st["cell_w"]
        y = st["y"]
        h = st["h"]
        color = st["color_map"].get(pid, "#cccccc")

        # Draw process block
        self.gantt_canvas.create_rectangle(x0, y, x1, y + h, fill=color, outline="#333")
        self.gantt_canvas.create_text((x0 + x1)/2, y + h/2, text=pid,
                                      font=("Segoe UI", 9, "bold"),
                                      fill="#fff" if pid != "Idle" else "#333")

        # Move to next unit after short delay
        st["index"] += 1
        self.root.after(80, self._animate_step)

    # ---------------------------------------------------
    # Draw time markings below the Gantt chart
    # ---------------------------------------------------
    def _draw_time_markers(self, per_unit, start_x, y, cell_w):
        tick_y = y + 60
        for i in range(len(per_unit) + 1):
            x = start_x + i * cell_w
            self.gantt_canvas.create_line(x, tick_y, x, tick_y+6, fill="#666")
            self.gantt_canvas.create_text(x + cell_w/2, tick_y + 16, text=str(i), font=("Segoe UI", 9))

    # ---------------------------------------------------
    # Display individual process statistics (dropdown)
    # ---------------------------------------------------
    def show_selected_process_stats(self, event=None):
        pid = self.selected_pid.get()
        for p in self.proc_results:
            if p["pid"] == pid:
                self.single_proc_label.config(
                    text=f"{pid} → Turnaround Time: {p['tat']} | Waiting Time: {p['wt']}",
                    fg="#0f4c81", font=("Segoe UI", 10, "bold")
                )
                return

# ---------------------------------------------------
# Run the application
# ---------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = SRTFApp(root)
    root.mainloop()
