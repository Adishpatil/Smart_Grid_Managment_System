# ⚡ Smart City Energy Grid Management System

A modern, Python-based Smart City Energy Grid simulator designed to model electricity distribution across a metropolitan network. It uses graph-based algorithms to calculate shortest transmission paths, manage supply and demand, and optimize load balancing across generation plants, substations, and city consumption zones.

## 🚀 Features

- **✅ Real Use Case Modeling**: Simulates a city's power grid with Generation (Power Plants), Substations, and City Zones (Consumers).
- **✅ Modern GUI**: Built with `ttkbootstrap` for a sleek, dark-themed, and responsive interface.
- **✅ Advanced Load Balancing**: Distributes electricity dynamically based on generation limits and city demands using Network Simplex (Min-Cost Flow).
- **✅ Transmission Realism**: Edges represent transmission lines with distance (loss) and maximum transmission capacity.
- **✅ Natural Graph Layout**: Automatically visualizes the grid in a natural layout using `networkx.spring_layout`.
- **✅ Path Optimization**: Uses Dijkstra’s Algorithm to find the shortest routing path with the least transmission loss.
- **✅ Persistent Storage**: SQLite database integration to automatically save and restore grid state, alongside detailed CSV logging.

## 🛠️ Tech Stack

- **Language**: Python 3
- **GUI framework**: `tkinter` & `ttkbootstrap` (Darkly Theme)
- **Algorithms**: Dijkstra’s Algorithm, Min-Cost Flow (`networkx`)
- **Database**: SQLite3
- **Logging**: Python `csv` module

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/Smart-City-Energy-Grid.git
   cd Smart-City-Energy-Grid
   ```

2. **Create a virtual environment (optional but recommended)**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## ▶️ Usage

Start the simulator by running the main script:
```bash
python main.py
```

### How to Simulate:
1. **Add Transmission Lines**: Go to the *Grid Editor* tab and add edges (e.g., From `G1` to `S1` with Loss `10` and Capacity `500`).
2. **Configure Nodes**: Assign roles and capacities to your nodes:
   - **Generation**: Positive capacity (e.g., `1000` MW)
   - **City Zone**: Negative capacity (Demand, e.g., `-300` MW)
   - **Substation**: Zero capacity (Routing/Storage)
3. **Run Load Balancing**: Switch to the *Load Balancing* tab and click `Run Load Balancing` to calculate the optimal power flow from Generation to City Zones.
4. **Check Energy Balance**: Instantly verify if the grid is stable or facing a blackout risk.

## 📁 Project Structure

```text
smart-city-energy-grid/
│
├── main.py              # Application entry point
├── gui.py               # Modern UI layout, styling, and event handlers
├── graph_logic.py       # Core logic: spring layout, Dijkstra, load balancing
├── db.py                # SQLite database management for grid persistence
├── logger.py            # CSV-based logging for history tracking
├── requirements.txt     # Python dependencies (networkx, ttkbootstrap)
├── .gitignore           # Ignores logs, db, and cache files
└── README.md            # Project documentation
```

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
