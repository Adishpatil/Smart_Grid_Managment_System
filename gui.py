import tkinter as tk
from tkinter import ttk, messagebox
from graph_logic import (
    graph, node_roles, add_edge, bulk_add_edges,
    dijkstra, update_node_role, update_node_capacity,
    get_node_roles, get_node_capacity, get_all_nodes
)
import math
import csv
from logger import log_edge, log_bulk_edges, log_node_role, log_load_balancing_result

class SmartGridVisualizer:

    def __init__(self, root):
        self.root = root
        self.root.title("Smart Grid Visualizer (Directed + Load Balancing)")
        self.root.geometry("900x700")

        # Scrollable Frame Setup
        self.main_canvas = tk.Canvas(self.root, borderwidth=0, background="#ffffff")
        self.scroll_frame = tk.Frame(self.main_canvas, background="#ffffff")
        self.vsb = tk.Scrollbar(self.root, orient="vertical", command=self.main_canvas.yview)
        self.main_canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.main_canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw", tags="self.scroll_frame")

        self.scroll_frame.bind("<Configure>", lambda event: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all")))

        # Now setup GUI components inside scroll_frame
        self.setup_gui()

    def setup_gui(self):
        self.canvas = tk.Canvas(self.scroll_frame, bg="white", width=650, height=400)
        self.canvas.pack(pady=10)

        self.main_frame = tk.Frame(self.scroll_frame)
        self.main_frame.pack()

        tk.Label(self.main_frame, text="Add Edge (From → To)", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=6)

        self.from_var = tk.StringVar()
        self.to_var = tk.StringVar()
        self.weight_var = tk.StringVar()

        self.from_entry = tk.Entry(self.main_frame, textvariable=self.from_var, width=5)
        self.to_entry = tk.Entry(self.main_frame, textvariable=self.to_var, width=5)
        self.weight_entry = tk.Entry(self.main_frame, textvariable=self.weight_var, width=5)

        self.from_entry.grid(row=1, column=0)
        tk.Label(self.main_frame, text="→").grid(row=1, column=1)
        self.to_entry.grid(row=1, column=2)
        tk.Label(self.main_frame, text="Weight").grid(row=1, column=3)
        self.weight_entry.grid(row=1, column=4)
        tk.Button(self.main_frame, text="Add", command=self.add_edge_gui).grid(row=1, column=5)

        tk.Label(self.main_frame, text="Bulk Add (Format: A B 10 Powerhouse 100 Substation 0)", font=("Arial", 10)).grid(row=2, column=0, columnspan=6)
        self.bulk_text = tk.Text(self.main_frame, height=5, width=60)
        self.bulk_text.grid(row=3, column=0, columnspan=5)
        tk.Button(self.main_frame, text="Bulk Add", command=self.bulk_add_gui).grid(row=3, column=5)

        tk.Label(self.main_frame, text="Set Node Role & Capacity", font=("Arial", 12, "bold")).grid(row=4, column=0, columnspan=6, pady=(10, 0))
        self.role_node_var = tk.StringVar()
        self.role_var = tk.StringVar(value="Powerhouse")
        self.capacity_var = tk.StringVar()

        tk.Entry(self.main_frame, textvariable=self.role_node_var, width=10).grid(row=5, column=0, columnspan=2)
        ttk.Combobox(self.main_frame, textvariable=self.role_var, values=["Powerhouse", "Substation", "Consumer"], state="readonly", width=12).grid(row=5, column=2, columnspan=2)
        tk.Entry(self.main_frame, textvariable=self.capacity_var, width=6).grid(row=5, column=4)
        tk.Button(self.main_frame, text="Assign", command=self.assign_role_capacity).grid(row=5, column=5)

        tk.Label(self.main_frame, text="Path Finder", font=("Arial", 12, "bold")).grid(row=6, column=0, columnspan=6, pady=(10, 0))
        self.src_var = tk.StringVar()
        self.dst_var = tk.StringVar()
        self.source_dropdown = ttk.Combobox(self.main_frame, textvariable=self.src_var, state="readonly", width=10)
        self.dest_dropdown = ttk.Combobox(self.main_frame, textvariable=self.dst_var, state="readonly", width=10)
        self.source_dropdown.grid(row=7, column=0, columnspan=2)
        self.dest_dropdown.grid(row=7, column=2, columnspan=2)
        tk.Button(self.main_frame, text="Find Path", command=self.find_path).grid(row=7, column=4, columnspan=2)

        self.result = tk.Label(self.scroll_frame, text="", font=("Arial", 11), fg="green")
        self.result.pack(pady=10)

        self.load_summary = tk.Text(self.scroll_frame, height=8, width=90, bg="#f4f4f4", font=("Courier", 9))
        self.load_summary.pack(pady=(0, 10))
        tk.Button(self.scroll_frame, text="Perform Load Balancing", command=self.perform_load_balancing).pack(pady=(0, 10))

    def update_dropdowns(self):
        all_nodes = get_all_nodes()
        self.source_dropdown['values'] = all_nodes
        self.dest_dropdown['values'] = all_nodes

    def add_edge_gui(self):
        from_node = self.from_var.get().strip()
        to_node = self.to_var.get().strip()
        weight = self.weight_var.get().strip()
        if not from_node or not to_node or not weight.isdigit():
            messagebox.showerror("Error", "Invalid input.")
            return
        add_edge(from_node, to_node, int(weight))
        self.from_var.set("")
        self.to_var.set("")
        self.weight_var.set("")
        self.update_dropdowns()
        self.redraw_graph()
        log_edge(from_node, to_node, weight)

    def bulk_add_gui(self):
        lines = self.bulk_text.get("1.0", "end-1c").splitlines()
        bulk_add_edges(lines)
        self.bulk_text.delete("1.0", "end")
        self.update_dropdowns()
        self.redraw_graph()
        log_bulk_edges(lines)

    def assign_role_capacity(self):
        node = self.role_node_var.get().strip()
        role = self.role_var.get()
        capacity = self.capacity_var.get().strip()
        if node:
            update_node_role(node, role)
            if capacity.lstrip("-").isdigit():
                update_node_capacity(node, int(capacity))
            self.role_node_var.set("")
            self.capacity_var.set("")
            self.redraw_graph()
            self.display_load_balancing()
        update_node_role(node, role)
        update_node_capacity(node, int(capacity))
        log_node_role(node, role, capacity)

    def find_path(self):
        source = self.src_var.get()
        dest = self.dst_var.get()
        if source not in get_all_nodes() or dest not in get_all_nodes():
            messagebox.showerror("Error", "Source or destination not in graph.")
            return
        path, dist = dijkstra(graph, source, dest)
        if path:
            self.result.config(text=f"Path: {' → '.join(path)}\nTotal Loss: {dist}")
        else:
            self.result.config(text="No path found")
        self.redraw_graph(path)

    def display_load_balancing(self):
        lines = ["Node       Role         Capacity         Demand/Supply"]
        for node in get_all_nodes():
            role = node_roles.get(node, "Unknown")
            capacity = get_node_capacity(node)
            if capacity < 0:
                status = f"Demand: {abs(capacity)}"
            elif capacity > 0:
                status = f"Supply: {capacity}"
            else:
                status = "Neutral"
            lines.append(f"{node:<10} {role:<12} {capacity:<10} {status}")
        self.load_summary.delete("1.0", "end")
        self.load_summary.insert("1.0", "\n".join(lines))

    def redraw_graph(self, highlight_path=None):
        self.canvas.delete("all")
        nodes = get_all_nodes()
        cols = int(math.ceil(math.sqrt(len(nodes))))
        rows = int(math.ceil(len(nodes) / cols))
        h_gap = 600 / (cols + 1)
        v_gap = 400 / (rows + 1)
        positions = {}

        for i, node in enumerate(nodes):
            row, col = divmod(i, cols)
            x = (col + 1) * h_gap
            y = (row + 1) * v_gap
            positions[node] = (x, y)

        for node in graph:
            for neighbor, weight in graph[node].items():
                x1, y1 = positions[node]
                x2, y2 = positions[neighbor]
                color = "red" if highlight_path and node in highlight_path and neighbor in highlight_path and highlight_path.index(neighbor) - highlight_path.index(node) == 1 else "black"
                width = 3 if color == "red" else 1
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width, arrow=tk.LAST)
                self.canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2, text=str(weight), fill="blue")

        for node in nodes:
            x, y = positions[node]
            role = node_roles.get(node, "Unknown")
            capacity = get_node_capacity(node)
            self.canvas.create_oval(x - 20, y - 20, x + 20, y + 20, fill="lightyellow")
            self.canvas.create_text(x, y - 12, text=node, font=("Arial", 10, "bold"))
            self.canvas.create_text(x, y, text=role, font=("Arial", 8, "italic"))
            self.canvas.create_text(x, y + 12, text=f"Cap: {capacity}", font=("Arial", 8), fill="darkgreen")
    def perform_load_balancing(self):
        supply_nodes = {n: get_node_capacity(n) for n in get_all_nodes() if get_node_capacity(n) > 0}
        demand_nodes = {n: -get_node_capacity(n) for n in get_all_nodes() if get_node_capacity(n) < 0}
        allocation_paths = []
        allocation = {}

        # Perform load balancing and allocate resources from supply nodes to demand nodes
        for consumer in demand_nodes:
            remaining_demand = demand_nodes[consumer]
            for powerhouse in supply_nodes:
                if remaining_demand == 0:
                    break
                supply = supply_nodes[powerhouse]
                if supply <= 0:
                    continue
                allocated = min(remaining_demand, supply)
                remaining_demand -= allocated
                supply_nodes[powerhouse] -= allocated
                allocation[consumer] = allocation.get(consumer, 0) + allocated
                allocation_paths.append((powerhouse, consumer, allocated))

        # Log results to CSV file
        log_load_balancing_result(allocation_paths)

        # Update the UI with the latest load balancing status
        self.display_load_balancing()

        return allocation_paths

    def log_load_balancing_results_to_csv(self, allocation_paths):
        # Define the CSV file path where the load balancing data will be stored
        file_path = "load_balancing_results.csv"
        
        # Open the CSV file in append mode, to avoid overwriting existing data
        with open(file_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            
            # Write the header if the file is empty
            if file.tell() == 0:
                writer.writerow(["Powerhouse", "Consumer", "Allocated"])

            # Write each allocation path (Powerhouse, Consumer, Allocation)
            for path in allocation_paths:
                writer.writerow(path)

if __name__ == "__main__":
    root = tk.Tk()
    app = SmartGridVisualizer(root)
    root.mainloop()
def check_energy_balance(self):
    total_supply = 0
    total_demand = 0
    total_storage = 0

    for node, attr in self.graph.nodes(data=True):
        role = attr.get('role')
        capacity = attr.get('capacity', 0)

        if role == "Supplier":
            total_supply += capacity
        elif role == "Consumer":
            total_demand += abs(capacity)
        elif role == "Substation":
            total_storage += capacity  # Stored energy

    if total_supply + total_storage < total_demand:
        tk.messagebox.showerror("Energy Error", f"⚠️ Insufficient Energy!\nTotal Supply ({total_supply}) + Storage ({total_storage}) < Total Demand ({total_demand})")
        return False
    else:
        return True
