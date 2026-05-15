import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import math

from graph_logic import (
    graph, node_roles, edge_capacities,
    add_edge, bulk_add_edges, dijkstra,
    update_node_role, update_node_capacity,
    get_node_capacity, get_all_nodes, compute_graph_layout
)
from logger import log_edge, log_bulk_edges, log_node_role, log_load_balancing_result
from db import (
    init_db, save_edge, save_node, save_load_balancing,
    load_edges, load_nodes, get_load_balancing_history, clear_all,
)

ROLE_COLORS = {
    "Generation": "#e74c3c",  # Red
    "Substation": "#f39c12",  # Orange
    "City Zone":  "#2ecc71",  # Green
    "Unknown":    "#7f8c8d",  # Gray
}

CANVAS_BG = "#222222"

class SmartGridVisualizer:
    def __init__(self, root):
        self.root = root
        init_db()
        self._build_ui()
        self._load_from_db()

    def _build_ui(self):
        # Header
        hdr = tb.Frame(self.root, padding=10, bootstyle="dark")
        hdr.pack(fill=X)
        tb.Label(hdr, text="⚡ Smart City Energy Grid", font=("Helvetica", 18, "bold"), bootstyle="inverse-dark").pack(side=LEFT, padx=10)
        
        self.status_var = tk.StringVar(value="Ready")
        tb.Label(hdr, textvariable=self.status_var, font=("Helvetica", 10), bootstyle="secondary-inverse").pack(side=RIGHT, padx=10)

        # Notebook
        nb = tb.Notebook(self.root, bootstyle="info")
        nb.pack(fill=BOTH, expand=True, padx=10, pady=10)

        tab_grid = tb.Frame(nb)
        tab_lb   = tb.Frame(nb)
        tab_hist = tb.Frame(nb)
        nb.add(tab_grid, text=" Grid Editor ")
        nb.add(tab_lb,   text=" Load Balancing ")
        nb.add(tab_hist, text=" History ")

        self._build_editor_tab(tab_grid)
        self._build_lb_tab(tab_lb)
        self._build_history_tab(tab_hist)

    def _build_editor_tab(self, parent):
        left = tb.Frame(parent, width=320)
        left.pack(side=LEFT, fill=Y, padx=5, pady=5)
        left.pack_propagate(False)

        right = tb.Frame(parent)
        right.pack(side=LEFT, fill=BOTH, expand=True)

        self.canvas = tk.Canvas(right, bg=CANVAS_BG, highlightthickness=0)
        self.canvas.pack(fill=BOTH, expand=True, padx=5, pady=5)
        self.canvas.bind("<Configure>", lambda _e: self.redraw_graph())

        # Scrollable container for tools
        container = tb.Frame(left)
        container.pack(fill=BOTH, expand=True)

        # Add Edge
        ef = tb.Frame(container)
        ef.pack(fill=X, pady=10, padx=5)
        tb.Label(ef, text=" ⚡ Add Transmission Line ", bootstyle="info-inverse", font=("Helvetica", 10, "bold"), padding=5).pack(fill=X, pady=(0, 5))
        
        self.from_var = tk.StringVar()
        self.to_var   = tk.StringVar()
        self.weight_var = tk.StringVar()
        self.cap_var = tk.StringVar(value="1000")
        
        for lbl, var in [("From Node:", self.from_var), ("To Node:", self.to_var), ("Loss (dist):", self.weight_var), ("Max Cap:", self.cap_var)]:
            row = tb.Frame(ef)
            row.pack(fill=X, pady=2)
            tb.Label(row, text=lbl, width=12).pack(side=LEFT)
            tb.Entry(row, textvariable=var, bootstyle="dark").pack(side=LEFT, fill=X, expand=True, padx=5)
        tb.Button(ef, text="Add Line", bootstyle="success", command=self.add_edge_gui).pack(fill=X, pady=(10,0))

        # Bulk Add
        bf = tb.Frame(container)
        bf.pack(fill=X, pady=10, padx=5)
        tb.Label(bf, text=" 📝 Bulk Add Edges ", bootstyle="secondary-inverse", font=("Helvetica", 10, "bold"), padding=5).pack(fill=X, pady=(0, 5))
        tb.Label(bf, text="Format: From To Loss MaxCap [RoleFrom CapFrom RoleTo CapTo]", font=("Courier", 8)).pack(fill=X, pady=2)
        self.bulk_text = tb.Text(bf, height=4, width=28, font=("Courier", 9))
        self.bulk_text.pack(fill=X, pady=5)
        tb.Button(bf, text="Bulk Import", bootstyle="info", command=self.bulk_add_gui).pack(fill=X)

        # Node Settings
        nf = tb.Frame(container)
        nf.pack(fill=X, pady=10, padx=5)
        tb.Label(nf, text=" ⚙️ Configure Node ", bootstyle="warning-inverse", font=("Helvetica", 10, "bold"), padding=5).pack(fill=X, pady=(0, 5))
        self.role_node_var = tk.StringVar()
        self.role_var      = tk.StringVar(value="Generation")
        self.capacity_var  = tk.StringVar()
        
        r1 = tb.Frame(nf)
        r1.pack(fill=X, pady=2)
        tb.Label(r1, text="Node ID:", width=12).pack(side=LEFT)
        tb.Entry(r1, textvariable=self.role_node_var, bootstyle="dark").pack(side=LEFT, fill=X, expand=True, padx=5)
        
        r2 = tb.Frame(nf)
        r2.pack(fill=X, pady=2)
        tb.Label(r2, text="Role:", width=12).pack(side=LEFT)
        cb = tb.Combobox(r2, textvariable=self.role_var, values=["Generation", "Substation", "City Zone"], state="readonly", bootstyle="dark")
        cb.pack(side=LEFT, fill=X, expand=True, padx=5)
        
        r3 = tb.Frame(nf)
        r3.pack(fill=X, pady=2)
        tb.Label(r3, text="Capacity:", width=12).pack(side=LEFT)
        tb.Entry(r3, textvariable=self.capacity_var, bootstyle="dark").pack(side=LEFT, fill=X, expand=True, padx=5)
        
        tb.Button(nf, text="Assign Role", bootstyle="warning", command=self.assign_role_capacity).pack(fill=X, pady=(10,0))

        # Path Finder
        pf = tb.Frame(container)
        pf.pack(fill=X, pady=10, padx=5)
        tb.Label(pf, text=" 📍 Find Shortest Path ", bootstyle="danger-inverse", font=("Helvetica", 10, "bold"), padding=5).pack(fill=X, pady=(0, 5))
        self.src_var = tk.StringVar()
        self.dst_var = tk.StringVar()
        
        pr1 = tb.Frame(pf)
        pr1.pack(fill=X, pady=2)
        tb.Label(pr1, text="Source:", width=12).pack(side=LEFT)
        self.source_dropdown = tb.Combobox(pr1, textvariable=self.src_var, state="readonly", bootstyle="dark")
        self.source_dropdown.pack(side=LEFT, fill=X, expand=True, padx=5)
        
        pr2 = tb.Frame(pf)
        pr2.pack(fill=X, pady=2)
        tb.Label(pr2, text="Target:", width=12).pack(side=LEFT)
        self.dest_dropdown = tb.Combobox(pr2, textvariable=self.dst_var, state="readonly", bootstyle="dark")
        self.dest_dropdown.pack(side=LEFT, fill=X, expand=True, padx=5)
        
        tb.Button(pf, text="Calculate Path", bootstyle="danger", command=self.find_path).pack(fill=X, pady=(10,0))
        
        self.result_var = tk.StringVar()
        tb.Label(pf, textvariable=self.result_var, bootstyle="success", wraplength=280).pack(pady=5)

        # Bottom Tools
        tb.Button(container, text="Reset Grid", bootstyle="secondary", command=self.reset_grid).pack(fill=X, pady=10)

    def _build_lb_tab(self, parent):
        toolbar = tb.Frame(parent, padding=10)
        toolbar.pack(fill=X)
        tb.Button(toolbar, text="Run Load Balancing", bootstyle="primary", command=self.perform_load_balancing).pack(side=LEFT, padx=5)
        tb.Button(toolbar, text="Check Energy Balance", bootstyle="info", command=self.check_energy_balance).pack(side=LEFT, padx=5)

        self.load_summary = tb.Text(parent, font=("Courier", 10), wrap="word")
        self.load_summary.pack(fill=BOTH, expand=True, padx=10, pady=10)

    def _build_history_tab(self, parent):
        toolbar = tb.Frame(parent, padding=10)
        toolbar.pack(fill=X)
        tb.Label(toolbar, text="Load Balancing DB History", font=("Helvetica", 12, "bold")).pack(side=LEFT)
        tb.Button(toolbar, text="Refresh", bootstyle="secondary", command=self.refresh_history).pack(side=RIGHT)

        cols = ("Timestamp", "Source", "Target", "Amount (MW)")
        self.history_tree = tb.Treeview(parent, columns=cols, show="headings", bootstyle="info")
        for col in cols:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, anchor=CENTER)

        vsb = tb.Scrollbar(parent, orient=VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=vsb.set)
        
        self.history_tree.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=10)
        vsb.pack(side=RIGHT, fill=Y, pady=10, padx=(0,10))
        self.refresh_history()

    def _load_from_db(self):
        edges = load_edges()
        nodes = load_nodes()
        for edge in edges:
            if len(edge) == 4:
                add_edge(edge[0], edge[1], edge[2], edge[3])
            else:
                add_edge(edge[0], edge[1], edge[2], 1000)
        for node, role, capacity in nodes:
            update_node_role(node, role)
            update_node_capacity(node, capacity)
        self._update_dropdowns()
        self.redraw_graph()
        self._set_status(f"Restored {len(edges)} edges and {len(nodes)} nodes")

    def refresh_history(self):
        for row in self.history_tree.get_children():
            self.history_tree.delete(row)
        for row in get_load_balancing_history():
            self.history_tree.insert("", tk.END, values=row)

    def _set_status(self, msg):
        self.status_var.set(msg)

    def _update_dropdowns(self):
        nodes = get_all_nodes()
        self.source_dropdown["values"] = nodes
        self.dest_dropdown["values"]   = nodes

    def add_edge_gui(self):
        u = self.from_var.get().strip()
        v = self.to_var.get().strip()
        w = self.weight_var.get().strip()
        c = self.cap_var.get().strip()
        if not u or not v or not w.isdigit() or not c.isdigit():
            messagebox.showerror("Error", "Fill all fields correctly.")
            return
        add_edge(u, v, int(w), int(c))
        save_edge(u.upper(), v.upper(), int(w), int(c))
        log_edge(u, v, w, c)
        self.from_var.set(""); self.to_var.set(""); self.weight_var.set("")
        self._update_dropdowns()
        self.redraw_graph()
        self._set_status(f"Line {u.upper()} -> {v.upper()} added")

    def bulk_add_gui(self):
        lines = [l for l in self.bulk_text.get("1.0", "end-1c").splitlines() if l.strip()]
        if not lines:
            return
        bulk_add_edges(lines)
        log_bulk_edges(lines)
        self.bulk_text.delete("1.0", "end")
        self._update_dropdowns()
        self.redraw_graph()
        self._set_status(f"Bulk added {len(lines)} edge(s)")

    def assign_role_capacity(self):
        node     = self.role_node_var.get().strip()
        role     = self.role_var.get()
        capacity = self.capacity_var.get().strip()
        if not node:
            messagebox.showerror("Error", "Node ID required.")
            return
        if not capacity.lstrip("-").isdigit():
            messagebox.showerror("Error", "Capacity must be integer (negative = demand).")
            return
        update_node_role(node, role)
        update_node_capacity(node, int(capacity))
        save_node(node.upper(), role, int(capacity))
        log_node_role(node, role, capacity)
        self.role_node_var.set(""); self.capacity_var.set("")
        self.redraw_graph()
        self._display_load_table()
        self._set_status(f"Node {node.upper()} updated")

    def find_path(self):
        source = self.src_var.get()
        dest   = self.dst_var.get()
        if source not in get_all_nodes() or dest not in get_all_nodes():
            messagebox.showerror("Error", "Source or target not in grid.")
            return
        path, dist = dijkstra(graph, source, dest)
        if path:
            self.result_var.set(f"Path: {' ➔ '.join(path)}\nTotal Loss: {dist}")
        else:
            self.result_var.set("No viable route.")
        self.redraw_graph(path)

    def reset_grid(self):
        if not messagebox.askyesno("Reset Grid", "Wipe entire grid and database?"):
            return
        clear_all()
        graph.clear()
        node_roles.clear()
        from graph_logic import node_capacities, all_nodes, edge_capacities
        node_capacities.clear()
        edge_capacities.clear()
        all_nodes.clear()
        self.canvas.delete("all")
        self._update_dropdowns()
        self.load_summary.delete("1.0", "end")
        self.result_var.set("")
        self.refresh_history()
        self._set_status("Grid Reset")

    def perform_load_balancing(self):
        from graph_logic import perform_load_balancing
        paths, display = perform_load_balancing()
        if not paths and "Error" in display:
            messagebox.showerror("Balancing Error", display)
            return

        if paths:
            log_load_balancing_result(paths)
            save_load_balancing(paths)
        
        self.load_summary.delete("1.0", "end")
        self.load_summary.insert("end", display + "\n\n" + "-"*50 + "\nALLOCATIONS:\n")
        if paths:
            for ph, cn, amt in paths:
                self.load_summary.insert("end", f"  {ph} ➔ {cn} : {amt} MW\n")
        else:
            self.load_summary.insert("end", "  No allocations needed/possible.\n")
            
        self.refresh_history()
        self._set_status("Load balancing completed.")

    def check_energy_balance(self):
        total_supply = sum(get_node_capacity(n) for n in get_all_nodes() if get_node_capacity(n) > 0)
        total_demand = sum(abs(get_node_capacity(n)) for n in get_all_nodes() if get_node_capacity(n) < 0)
        
        if total_supply < total_demand:
            messagebox.showerror("Blackout Risk",
                f"Deficit detected!\n\n"
                f"  Total Generation : {total_supply} MW\n"
                f"  Total Demand     : {total_demand} MW\n\n"
                f"  Shortfall        : {total_demand - total_supply} MW")
            return False
        messagebox.showinfo("Grid Stable",
            f"  Total Generation : {total_supply} MW\n"
            f"  Total Demand     : {total_demand} MW\n\n"
            f"  Surplus          : {total_supply - total_demand} MW")
        return True

    def _display_load_table(self):
        from graph_logic import display_load_balancing
        display = display_load_balancing()
        self.load_summary.delete("1.0", "end")
        self.load_summary.insert("1.0", display + "\n")

    def redraw_graph(self, highlight_path=None):
        self.canvas.delete("all")
        nodes = get_all_nodes()
        if not nodes:
            return
            
        w = self.canvas.winfo_width() or 800
        h = self.canvas.winfo_height() or 600
        
        pos = compute_graph_layout(w, h, padding=50)

        # Draw edges
        for u in graph:
            for v, weight in graph[u].items():
                if u not in pos or v not in pos: continue
                x1, y1 = pos[u]
                x2, y2 = pos[v]
                is_hl = (highlight_path and u in highlight_path and v in highlight_path and highlight_path.index(v) - highlight_path.index(u) == 1)
                color = "#3498db" if is_hl else "#555555"
                width = 4 if is_hl else 2
                
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width, arrow=tk.LAST, smooth=True)
                
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                cap = edge_capacities.get((u, v), 1000)
                txt = f"L:{weight}\nC:{cap}"
                self.canvas.create_rectangle(mx-15, my-15, mx+15, my+15, fill="#111111", outline="")
                self.canvas.create_text(mx, my, text=txt, fill="#aaaaaa", font=("Helvetica", 7))

        # Draw nodes
        R = 24
        for node in nodes:
            x, y = pos[node]
            role = node_roles.get(node, "Unknown")
            cap = get_node_capacity(node)
            color = ROLE_COLORS.get(role, ROLE_COLORS["Unknown"])
            
            # Glow effect
            self.canvas.create_oval(x-R-5, y-R-5, x+R+5, y+R+5, fill=color, outline="", stipple="gray25")
            self.canvas.create_oval(x-R, y-R, x+R, y+R, fill="#333333", outline=color, width=3)
            
            self.canvas.create_text(x, y-5, text=node, fill="white", font=("Helvetica", 10, "bold"))
            
            if cap != 0:
                self.canvas.create_text(x, y+10, text=f"{cap} MW", fill="#dddddd", font=("Helvetica", 8))

        # Legend
        lx, ly = 20, 20
        for role, color in ROLE_COLORS.items():
            self.canvas.create_oval(lx, ly, lx+12, ly+12, fill=color, outline="")
            self.canvas.create_text(lx+20, ly+6, text=role, fill="white", anchor=tk.W, font=("Helvetica", 9))
            ly += 22
