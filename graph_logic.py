import heapq
import networkx as nx

graph = {}
node_roles = {}
node_capacities = {}
edge_capacities = {}
all_nodes = set()

def add_edge(u, v, weight, max_capacity=1000):
    u = u.strip().upper()
    v = v.strip().upper()
    if u not in graph:
        graph[u] = {}
    if v not in graph:
        graph[v] = {}
    graph[u][v] = weight
    edge_capacities[(u, v)] = max_capacity
    all_nodes.update([u, v])

def bulk_add_edges(lines):
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 4:
            try:
                u, v = parts[0].upper(), parts[1].upper()
                weight = int(parts[2])
                max_cap = int(parts[3])
                
                role_u = parts[4] if len(parts) > 4 else "Unknown"
                cap_u = int(parts[5]) if len(parts) > 5 else 0
                role_v = parts[6] if len(parts) > 6 else "Unknown"
                cap_v = int(parts[7]) if len(parts) > 7 else 0
                
                add_edge(u, v, weight, max_cap)
                update_node_role(u, role_u)
                update_node_capacity(u, cap_u)
                update_node_role(v, role_v)
                update_node_capacity(v, cap_v)
            except ValueError:
                print(f"Invalid format in line: {line}")
        elif len(parts) >= 3:
            try:
                u, v = parts[0].upper(), parts[1].upper()
                weight = int(parts[2])
                add_edge(u, v, weight, 1000)
            except ValueError:
                pass

def update_node_role(node, role):
    node = node.strip().upper().strip('"')
    if node not in graph:
        graph[node] = {}
    all_nodes.add(node)
    node_roles[node] = role

def update_node_capacity(node, capacity):
    node = node.strip().upper().strip('"')
    if node not in graph:
        graph[node] = {}
    all_nodes.add(node)
    node_capacities[node] = capacity

def get_node_roles():
    for node in all_nodes:
        if node not in node_roles:
            node_roles[node] = "Unknown"
    return node_roles

def get_node_capacity(node):
    node = node.strip().upper().strip('"')
    return node_capacities.get(node, 0)

def get_all_nodes():
    return sorted(all_nodes)

def dijkstra(graph, start, end):
    start = start.strip().upper()
    end = end.strip().upper()
    queue = [(0, start, [])]
    visited = set()
    while queue:
        (cost, node, path) = heapq.heappop(queue)
        if node in visited:
            continue
        path = path + [node]
        visited.add(node)
        if node == end:
            return path, cost
        for adj, weight in graph.get(node, {}).items():
            if adj not in visited:
                heapq.heappush(queue, (cost + weight, adj, path))
    return None, float('inf')

def display_load_balancing():
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
        lines.append(f"{node:<10} {role:<14} {capacity:<10} {status}")
    return "\n".join(lines)

def perform_load_balancing():
    G = nx.DiGraph()

    # Add all edges with weight as cost and max_capacity as capacity
    for u in graph:
        for v in graph[u]:
            weight = graph[u][v]
            cap = edge_capacities.get((u, v), 1000)
            G.add_edge(u, v, weight=weight, capacity=cap)

    # Set node demands (positive = demand, negative = supply)
    for node in get_all_nodes():
        cap = get_node_capacity(node)
        if cap > 0:
            G.nodes[node]['demand'] = -cap  # supply
        elif cap < 0:
            G.nodes[node]['demand'] = abs(cap)  # demand
        else:
            G.nodes[node]['demand'] = 0

    total_supply = sum(cap for node, cap in node_capacities.items() if cap > 0)
    total_demand = sum(abs(cap) for node, cap in node_capacities.items() if cap < 0)
    
    dummy_node = "DUMMY_SINK"
    if total_supply > total_demand:
        excess = total_supply - total_demand
        G.add_node(dummy_node, demand=excess)
        for node in get_all_nodes():
            if get_node_capacity(node) > 0:
                G.add_edge(node, dummy_node, weight=0, capacity=excess)
    elif total_demand > total_supply:
        return [], "Error: Total demand exceeds total supply. Cannot fully balance the grid!"

    try:
        flowCost, flowDict = nx.network_simplex(G)
    except Exception as e:
        return [], f"Error in optimal load balancing: {e}"

    allocation_paths = []
    for u in flowDict:
        if u == dummy_node: continue
        for v in flowDict[u]:
            if v == dummy_node: continue
            amount = flowDict[u][v]
            if amount > 0:
                allocation_paths.append((u, v, amount))

    load_balancing_display = display_load_balancing()
    return allocation_paths, load_balancing_display

def compute_graph_layout(width, height, padding=60):
    G = nx.Graph()
    for u in graph:
        for v in graph[u]:
            G.add_edge(u, v)
            
    if not G.nodes:
        return {}
    
    # Using spring layout for a more natural network look
    pos = nx.spring_layout(G, seed=42)
    
    scaled_pos = {}
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    
    if not xs or not ys: return {}
        
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    range_x = max_x - min_x or 1
    range_y = max_y - min_y or 1
    
    draw_width = width - 2 * padding
    draw_height = height - 2 * padding
    
    for node, (x, y) in pos.items():
        scaled_x = padding + ((x - min_x) / range_x) * draw_width
        scaled_y = padding + ((y - min_y) / range_y) * draw_height
        scaled_pos[node] = (scaled_x, scaled_y)
        
    # Also add isolated nodes if any
    for i, node in enumerate(all_nodes):
        if node not in scaled_pos:
            scaled_pos[node] = (padding + (i*30) % draw_width, padding)
            
    return scaled_pos
