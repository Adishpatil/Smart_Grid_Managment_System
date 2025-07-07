import heapq
import networkx as nx

graph = {}
node_roles = {}
node_capacities = {}
all_nodes = set()

def add_edge(u, v, weight):
    u = u.strip().upper()
    v = v.strip().upper()
    if u not in graph:
        graph[u] = {}
    if v not in graph:
        graph[v] = {}
    graph[u][v] = weight
    all_nodes.update([u, v])

def bulk_add_edges(lines):
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 3:
            u, v, weight = parts[0].upper(), parts[1].upper(), int(parts[2])
            role_u = parts[3] if len(parts) > 3 else "Unknown"
            cap_u = int(parts[4]) if len(parts) > 4 else 0
            role_v = parts[5] if len(parts) > 5 else "Unknown"
            cap_v = int(parts[6]) if len(parts) > 6 else 0
            add_edge(u, v, weight)
            update_node_role(u, role_u)
            update_node_capacity(u, cap_u)
            update_node_role(v, role_v)
            update_node_capacity(v, cap_v)

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
        lines.append(f"{node:<10} {role:<12} {capacity:<10} {status}")
    return "\n".join(lines)

def perform_load_balancing():
    G = nx.DiGraph()

    # Add all edges with weight as cost and capacity set very high (simulate unlimited)
    for u in graph:
        for v in graph[u]:
            weight = graph[u][v]
            G.add_edge(u, v, weight=weight, capacity=9999)

    # Set node demands (positive = demand, negative = supply)
    for node in get_all_nodes():
        cap = get_node_capacity(node)
        if cap > 0:
            G.nodes[node]['demand'] = -cap  # supply
        elif cap < 0:
            G.nodes[node]['demand'] = abs(cap)  # demand
        else:
            G.nodes[node]['demand'] = 0

    # Solve min-cost flow
    try:
        flowCost, flowDict = nx.network_simplex(G)
    except Exception as e:
        return [], f"Error in optimal load balancing: {e}"

    allocation_paths = []
    for u in flowDict:
        for v in flowDict[u]:
            amount = flowDict[u][v]
            if amount > 0:
                allocation_paths.append((u, v, amount))

    load_balancing_display = display_load_balancing()
    return allocation_paths, load_balancing_display

