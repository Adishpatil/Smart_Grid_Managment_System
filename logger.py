import csv
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(r"C:\Users\ASUS\OneDrive\Desktop\SEM 4th\PBL-II\SGM\logs"))
LOG_DIR = os.path.join(BASE_DIR, "logs")
EDGE_FILE = os.path.join(LOG_DIR, "edges.csv")
NODE_FILE = os.path.join(LOG_DIR, "nodes.csv")
LOAD_FILE = os.path.join(LOG_DIR, "load_balancing.csv")

# Ensure the log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Helper function to get the current timestamp formatted
def get_timestamp():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def log_edge(from_node, to_node, weight):
    with open(EDGE_FILE, "a", newline='') as file:
        writer = csv.writer(file)
        writer.writerow([get_timestamp(), from_node, to_node, weight])

def log_bulk_edges(lines):
    with open(EDGE_FILE, "a", newline='') as file:
        writer = csv.writer(file)
        for line in lines:
            tokens = line.split()
            if len(tokens) >= 3:
                writer.writerow([get_timestamp()] + tokens[:3])

def log_node_role(node, role, capacity):
    with open(NODE_FILE, "a", newline='') as file:
        writer = csv.writer(file)
        writer.writerow([get_timestamp(), node, role, capacity])

def log_load_balancing_result(allocation_paths):
    with open(LOAD_FILE, "a", newline='') as file:
        writer = csv.writer(file)
        for from_node, to_node, amount in allocation_paths:
            writer.writerow([get_timestamp(), from_node, to_node, amount])
