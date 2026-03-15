# ⚡ Smart Grid Management System 🔌

A Python-based Smart Grid Management System designed to simulate electricity distribution across a power network using graph-based algorithms. This project allows users to create a grid of powerhouses, substations, and consumers, calculate shortest paths using Dijkstra's algorithm, and balance loads based on node capacities.

## 🚀 Features

- ✅ Graph-based electricity distribution network
- ✅ GUI built using Tkinter
- ✅ Node role assignment (Powerhouse, Substation, Consumer)
- ✅ Real-time distance-based edge weights (in kilometers)
- ✅ Dijkstra’s Algorithm for shortest path calculation
- ✅ Load balancing feature to distribute electricity based on supply and demand
- ✅ Bulk node and edge addition
- ✅ Dynamic dropdowns for source and destination selection
- ✅ Canvas and UI scrolling support
- ✅ Capacity-aware load distribution logic


## 🛠️ Tech Stack

- **Language**: Python 3
- **GUI**: Tkinter
- **Algorithm**: Dijkstra’s Algorithm (networkx optional)
- **Data Handling**: Custom dictionaries and logic (optional: SQLite/MySQL for persistence)


## 📁 Project Structure

smart-grid-management/
│
├── main.py              # Entry point
├── gui.py               # GUI layout and event handlers
├── graph_logic.py       # Core logic: graph structure, Dijkstra, load balancing
├── logger.py            # CSV-based logging for edges, nodes, and load balancing
├── requirements.txt     # Python dependencies
├── .gitignore           # Excludes logs and generated CSV files
├── README.md            # Project documentation
