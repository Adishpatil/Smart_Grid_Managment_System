import tkinter as tk
from tkinter import ttk, messagebox
import math

from graph_logic import (
    graph, node_roles,
    add_edge, bulk_add_edges, dijkstra,
    update_node_role, update_node_capacity,
    get_node_capacity, get_all_nodes,
)
from logger import log_edge, log_bulk_edges, log_node_role, log_load_balancing_result
from db import (
    init_db, save_edge, save_node, save_load_balancing,
    load_edges, load_nodes, get_load_balancing_history, clear_all,
)

ROLE_COLORS = {
    "Powerhouse": "#f72585",
    "Substation":  "#4cc9f0",
    "Consumer":    "#06d6a0",
    "Unknown":     "#adb5bd",
}
CANVAS_BG  = "#0f172a"
PANEL_BG   = "#1e293b"
TEXT_COLOR = "#e2e8f0"
DIM_COLOR  = "#64748b"


def _section(parent, title):
    """A simple titled card frame (replaces LabelFrame to avoid ttkbootstrap compat issues)."""
    outer = tk.Frame(parent, bg=PANEL_BG, bd=0)
    outer.pack(fill=tk.X, pady=(0, 8))
    tk.Label(outer, text=f"  {title}", bg="#334155", fg="#94a3b8",
             font=("Helvetica", 8, "bold"), anchor=tk.W).pack(fill=tk.X)
    inner = tk.Frame(outer, bg=PANEL_BG, padx=10, pady=8)
    inner.pack(fill=tk.X)
    return inner


def _btn(parent, text, cmd, color="#3b82f6", width=None):
    kw = dict(bg=color, fg="white", activebackground=color, activeforeground="white",
              font=("Helvetica", 9, "bold"), relief=tk.FLAT, cursor="hand2",
              padx=8, pady=4, command=cmd)
    if width:
        kw["width"] = width
    return tk.Button(parent, text=text, **kw)


class SmartGridVisualizer:

    def __init__(self, root):
        self.root = root
        self.root.configure(bg="#0f172a")
        init_db()
        self._build_ui()
        self._load_from_db()

    # ------------------------------------------------------------------ #
    #  UI CONSTRUCTION                                                     #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg="#1e293b", pady=10)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="  Smart Grid Management System",
                 bg="#1e293b", fg="white",
                 font=("Helvetica", 14, "bold")).pack(side=tk.LEFT, padx=10)
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(hdr, textvariable=self.status_var,
                 bg="#1e293b", fg=DIM_COLOR,
                 font=("Helvetica", 9)).pack(side=tk.RIGHT, padx=12)

        # Notebook
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook",        background="#0f172a", borderwidth=0)
        style.configure("TNotebook.Tab",    background="#1e293b", foreground="#94a3b8",
                                            padding=[12, 6], font=("Helvetica", 9))
        style.map("TNotebook.Tab",          background=[("selected", "#334155")],
                                            foreground=[("selected", "white")])

        nb = ttk.Notebook(self.root)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=(6, 10))

        tab_grid = tk.Frame(nb, bg="#0f172a")
        tab_lb   = tk.Frame(nb, bg="#0f172a")
        tab_hist = tk.Frame(nb, bg="#0f172a")
        nb.add(tab_grid, text="  Grid Editor  ")
        nb.add(tab_lb,   text=" Load Balancing ")
        nb.add(tab_hist, text="    History    ")

        self._build_editor_tab(tab_grid)
        self._build_lb_tab(tab_lb)
        self._build_history_tab(tab_hist)

    # ── Tab 1: Grid Editor ──────────────────────────────────────────────
    def _build_editor_tab(self, parent):
        left  = tk.Frame(parent, bg="#0f172a", width=260)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(8, 4), pady=8)
        left.pack_propagate(False)

        right = tk.Frame(parent, bg="#0f172a")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(right, bg=CANVAS_BG, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=(0, 8), pady=8)
        self.canvas.bind("<Configure>", lambda _e: self.redraw_graph())

        # Add Edge
        ef = _section(left, "Add Edge")
        self.from_var = tk.StringVar()
        self.to_var   = tk.StringVar()
        self.weight_var = tk.StringVar()
        row = tk.Frame(ef, bg=PANEL_BG)
        row.pack(fill=tk.X)
        for lbl, var, w in [("From", self.from_var, 5), ("To", self.to_var, 5), ("Weight", self.weight_var, 6)]:
            col = tk.Frame(row, bg=PANEL_BG)
            col.pack(side=tk.LEFT, padx=3)
            tk.Label(col, text=lbl, bg=PANEL_BG, fg=DIM_COLOR, font=("Helvetica", 8)).pack()
            tk.Entry(col, textvariable=var, width=w, bg="#334155", fg=TEXT_COLOR,
                     insertbackground="white", relief=tk.FLAT).pack()
        _btn(ef, "Add", self.add_edge_gui, "#22c55e").pack(side=tk.RIGHT, pady=(4, 0))

        # Bulk Add
        bf = _section(left, "Bulk Add Edges")
        tk.Label(bf, text="A B 10 Powerhouse 100 Consumer -50",
                 bg=PANEL_BG, fg=DIM_COLOR, font=("Courier", 7)).pack()
        self.bulk_text = tk.Text(bf, height=4, width=28, font=("Courier", 9),
                                  bg="#334155", fg="#94a3b8",
                                  insertbackground="white", relief=tk.FLAT)
        self.bulk_text.pack(pady=5)
        _btn(bf, "Bulk Add", self.bulk_add_gui, "#0ea5e9").pack(fill=tk.X)

        # Node Settings
        nf = _section(left, "Node Settings")
        self.role_node_var = tk.StringVar()
        self.role_var      = tk.StringVar(value="Powerhouse")
        self.capacity_var  = tk.StringVar()
        for lbl, widget_type, var, extra in [
            ("Node",     "entry",  self.role_node_var, {}),
            ("Role",     "combo",  self.role_var,      {}),
            ("Capacity", "entry",  self.capacity_var,  {}),
        ]:
            row = tk.Frame(nf, bg=PANEL_BG)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=lbl, width=8, bg=PANEL_BG, fg=DIM_COLOR,
                     font=("Helvetica", 8), anchor=tk.E).pack(side=tk.LEFT)
            if widget_type == "combo":
                cb = ttk.Combobox(row, textvariable=var,
                                  values=["Powerhouse", "Substation", "Consumer"],
                                  state="readonly", width=14)
                cb.pack(side=tk.LEFT, padx=4)
            else:
                tk.Entry(row, textvariable=var, width=12, bg="#334155", fg=TEXT_COLOR,
                         insertbackground="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=4)
        _btn(nf, "Assign", self.assign_role_capacity, "#f59e0b").pack(fill=tk.X, pady=(6, 0))

        # Path Finder
        pf = _section(left, "Path Finder  (Dijkstra)")
        self.src_var = tk.StringVar()
        self.dst_var = tk.StringVar()
        self.source_dropdown = ttk.Combobox(pf, textvariable=self.src_var, state="readonly", width=16)
        self.dest_dropdown   = ttk.Combobox(pf, textvariable=self.dst_var, state="readonly", width=16)
        for lbl, cb in [("From", self.source_dropdown), ("To", self.dest_dropdown)]:
            row = tk.Frame(pf, bg=PANEL_BG)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=lbl, width=5, bg=PANEL_BG, fg=DIM_COLOR,
                     font=("Helvetica", 8), anchor=tk.E).pack(side=tk.LEFT)
            cb.pack(side=tk.LEFT, padx=4)
        _btn(pf, "Find Shortest Path", self.find_path, "#ef4444").pack(fill=tk.X, pady=(6, 0))

        self.result_var = tk.StringVar()
        tk.Label(left, textvariable=self.result_var, bg="#0f172a", fg="#4ade80",
                 wraplength=240, font=("Helvetica", 9), justify=tk.LEFT).pack(pady=4, anchor=tk.W, padx=8)

        _btn(left, "Reset Grid", self.reset_grid, "#475569").pack(fill=tk.X, pady=(4, 0), padx=0)

    # ── Tab 2: Load Balancing ───────────────────────────────────────────
    def _build_lb_tab(self, parent):
        toolbar = tk.Frame(parent, bg="#0f172a", pady=8)
        toolbar.pack(fill=tk.X, padx=10)
        _btn(toolbar, "  Run Load Balancing", self.perform_load_balancing, "#f59e0b").pack(side=tk.LEFT, padx=(0, 8))
        _btn(toolbar, "Check Energy Balance", self.check_energy_balance,   "#0ea5e9").pack(side=tk.LEFT)

        self.load_summary = tk.Text(
            parent, font=("Courier", 10),
            bg="#0f172a", fg="#4ade80",
            insertbackground="white", relief=tk.FLAT, padx=12, pady=10,
        )
        self.load_summary.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    # ── Tab 3: History ──────────────────────────────────────────────────
    def _build_history_tab(self, parent):
        toolbar = tk.Frame(parent, bg="#0f172a", pady=8)
        toolbar.pack(fill=tk.X, padx=10)
        tk.Label(toolbar, text="Load Balancing History  (SQLite)",
                 bg="#0f172a", fg=TEXT_COLOR,
                 font=("Helvetica", 11, "bold")).pack(side=tk.LEFT)
        _btn(toolbar, "Refresh", self.refresh_history, "#334155").pack(side=tk.RIGHT)

        style = ttk.Style()
        style.configure("Treeview",
                         background="#1e293b", foreground=TEXT_COLOR,
                         fieldbackground="#1e293b", rowheight=24,
                         font=("Helvetica", 9))
        style.configure("Treeview.Heading",
                         background="#334155", foreground="#94a3b8",
                         font=("Helvetica", 9, "bold"))
        style.map("Treeview", background=[("selected", "#3b82f6")])

        cols = ("Timestamp", "From", "To", "Amount (units)")
        self.history_tree = ttk.Treeview(parent, columns=cols, show="headings")
        for col in cols:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=180, anchor=tk.CENTER)

        vsb = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=vsb.set)
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=(0, 10))
        vsb.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 10), padx=(0, 10))
        self.refresh_history()

    # ------------------------------------------------------------------ #
    #  DATABASE                                                            #
    # ------------------------------------------------------------------ #

    def _load_from_db(self):
        edges = load_edges()
        nodes = load_nodes()
        for from_node, to_node, weight in edges:
            add_edge(from_node, to_node, weight)
        for node, role, capacity in nodes:
            update_node_role(node, role)
            update_node_capacity(node, capacity)
        self._update_dropdowns()
        self.redraw_graph()
        self._set_status(f"Restored {len(edges)} edge(s) and {len(nodes)} node(s) from database")

    def refresh_history(self):
        for row in self.history_tree.get_children():
            self.history_tree.delete(row)
        for row in get_load_balancing_history():
            self.history_tree.insert("", tk.END, values=row)

    # ------------------------------------------------------------------ #
    #  HELPERS                                                             #
    # ------------------------------------------------------------------ #

    def _set_status(self, msg):
        self.status_var.set(msg)

    def _update_dropdowns(self):
        nodes = get_all_nodes()
        self.source_dropdown["values"] = nodes
        self.dest_dropdown["values"]   = nodes

    # ------------------------------------------------------------------ #
    #  ACTIONS                                                             #
    # ------------------------------------------------------------------ #

    def add_edge_gui(self):
        u = self.from_var.get().strip()
        v = self.to_var.get().strip()
        w = self.weight_var.get().strip()
        if not u or not v or not w.isdigit():
            messagebox.showerror("Error", "Fill From, To, and a numeric Weight.")
            return
        add_edge(u, v, int(w))
        save_edge(u.upper(), v.upper(), int(w))
        log_edge(u, v, w)
        self.from_var.set(""); self.to_var.set(""); self.weight_var.set("")
        self._update_dropdowns()
        self.redraw_graph()
        self._set_status(f"Edge  {u.upper()} -> {v.upper()}  (weight {w})  added")

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
            messagebox.showerror("Error", "Node name is required.")
            return
        if not capacity.lstrip("-").isdigit():
            messagebox.showerror("Error", "Capacity must be an integer (negative = demand).")
            return
        update_node_role(node, role)
        update_node_capacity(node, int(capacity))
        save_node(node.upper(), role, int(capacity))
        log_node_role(node, role, capacity)
        self.role_node_var.set(""); self.capacity_var.set("")
        self.redraw_graph()
        self._display_load_table()
        self._set_status(f"Node {node.upper()} -> {role},  capacity {capacity}")

    def find_path(self):
        source = self.src_var.get()
        dest   = self.dst_var.get()
        if source not in get_all_nodes() or dest not in get_all_nodes():
            messagebox.showerror("Error", "Source or destination not in graph.")
            return
        path, dist = dijkstra(graph, source, dest)
        if path:
            self.result_var.set(f"Path: {' -> '.join(path)}\nTotal Loss: {dist}")
        else:
            self.result_var.set("No path found.")
        self.redraw_graph(path)

    def reset_grid(self):
        if not messagebox.askyesno("Reset Grid", "Clear the graph AND the database. Continue?"):
            return
        clear_all()
        graph.clear()
        node_roles.clear()
        from graph_logic import node_capacities, all_nodes
        node_capacities.clear()
        all_nodes.clear()
        self.canvas.delete("all")
        self._update_dropdowns()
        self.load_summary.delete("1.0", "end")
        self.result_var.set("")
        self.refresh_history()
        self._set_status("Grid reset — database cleared")

    def perform_load_balancing(self):
        supply = {n: get_node_capacity(n) for n in get_all_nodes() if get_node_capacity(n) > 0}
        demand = {n: -get_node_capacity(n) for n in get_all_nodes() if get_node_capacity(n) < 0}
        allocation_paths = []
        for consumer, needed in demand.items():
            for powerhouse in list(supply):
                if needed == 0:
                    break
                available = supply[powerhouse]
                if available <= 0:
                    continue
                allocated = min(needed, available)
                needed -= allocated
                supply[powerhouse] -= allocated
                allocation_paths.append((powerhouse, consumer, allocated))

        log_load_balancing_result(allocation_paths)
        save_load_balancing(allocation_paths)
        self._display_load_table()
        self.refresh_history()
        lines = ["\n  ALLOCATION RESULTS", "-" * 44]
        if allocation_paths:
            for ph, cn, amt in allocation_paths:
                lines.append(f"  {ph:<10} ->  {cn:<10}  :  {amt} units")
        else:
            lines.append("  Nothing to allocate (no supply/demand nodes set).")
        self.load_summary.insert("end", "\n".join(lines) + "\n")
        self._set_status(f"Load balancing complete — {len(allocation_paths)} allocation(s) saved")
        return allocation_paths

    def check_energy_balance(self):
        total_supply = total_demand = total_storage = 0
        for node in get_all_nodes():
            role     = node_roles.get(node, "Unknown")
            capacity = get_node_capacity(node)
            if role == "Powerhouse":
                total_supply  += capacity
            elif role == "Consumer":
                total_demand  += abs(capacity)
            elif role == "Substation":
                total_storage += capacity
        if total_supply + total_storage < total_demand:
            messagebox.showerror("Energy Alert",
                f"Insufficient energy!\n\n"
                f"  Supply   : {total_supply}\n"
                f"  Storage  : {total_storage}\n"
                f"  Demand   : {total_demand}\n\n"
                f"  Shortfall: {total_demand - total_supply - total_storage} units")
            return False
        messagebox.showinfo("Energy Balance OK",
            f"  Supply   : {total_supply}\n"
            f"  Storage  : {total_storage}\n"
            f"  Demand   : {total_demand}\n\n"
            f"  Surplus  : {total_supply + total_storage - total_demand} units")
        return True

    # ------------------------------------------------------------------ #
    #  DRAW                                                                #
    # ------------------------------------------------------------------ #

    def _display_load_table(self):
        header = f"{'Node':<10} {'Role':<14} {'Capacity':>10}    Status"
        sep    = "-" * 48
        rows   = []
        for node in get_all_nodes():
            role     = node_roles.get(node, "Unknown")
            capacity = get_node_capacity(node)
            status   = (f"Demand : {abs(capacity)}" if capacity < 0
                        else f"Supply : {capacity}" if capacity > 0
                        else "Neutral")
            rows.append(f"{node:<10} {role:<14} {capacity:>10}    {status}")
        self.load_summary.delete("1.0", "end")
        self.load_summary.insert("1.0", "\n".join([header, sep] + rows) + "\n")

    def redraw_graph(self, highlight_path=None):
        self.canvas.delete("all")
        nodes = get_all_nodes()
        if not nodes:
            return
        w = self.canvas.winfo_width()  or 700
        h = self.canvas.winfo_height() or 450
        cols  = max(1, math.ceil(math.sqrt(len(nodes))))
        nrows = max(1, math.ceil(len(nodes) / cols))
        h_gap = w / (cols + 1)
        v_gap = h / (nrows + 1)

        pos = {}
        for i, node in enumerate(nodes):
            r, c = divmod(i, cols)
            pos[node] = ((c + 1) * h_gap, (r + 1) * v_gap)

        for u in graph:
            for v, weight in graph[u].items():
                if u not in pos or v not in pos:
                    continue
                x1, y1 = pos[u]
                x2, y2 = pos[v]
                is_hl = (highlight_path
                         and u in highlight_path and v in highlight_path
                         and highlight_path.index(v) - highlight_path.index(u) == 1)
                color = "#f8961e" if is_hl else "#334155"
                width = 3 if is_hl else 1.5
                self.canvas.create_line(x1, y1, x2, y2,
                                         fill=color, width=width, arrow=tk.LAST, smooth=True)
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                self.canvas.create_oval(mx-11, my-9, mx+11, my+9, fill="#1e293b", outline="")
                self.canvas.create_text(mx, my, text=str(weight),
                                         fill="#7dd3fc", font=("Helvetica", 8, "bold"))

        R = 26
        for node in nodes:
            x, y  = pos[node]
            role  = node_roles.get(node, "Unknown")
            cap   = get_node_capacity(node)
            color = ROLE_COLORS.get(role, ROLE_COLORS["Unknown"])
            self.canvas.create_oval(x-R-6, y-R-6, x+R+6, y+R+6,
                                     fill=color, outline="", stipple="gray25")
            self.canvas.create_oval(x-R, y-R, x+R, y+R,
                                     fill=color, outline="#e2e8f0", width=1.5)
            self.canvas.create_text(x, y-9,  text=node,     fill="white", font=("Helvetica", 10, "bold"))
            self.canvas.create_text(x, y+4,  text=role[:4], fill="white", font=("Helvetica", 7, "italic"))
            self.canvas.create_text(x, y+16, text=str(cap), fill="white", font=("Helvetica", 7))

        lx, ly = 12, h - 80
        for role, color in ROLE_COLORS.items():
            if role == "Unknown":
                continue
            self.canvas.create_oval(lx, ly, lx+12, ly+12, fill=color, outline="")
            self.canvas.create_text(lx+18, ly+6, text=role, fill="#94a3b8",
                                     font=("Helvetica", 8), anchor=tk.W)
            ly += 20
