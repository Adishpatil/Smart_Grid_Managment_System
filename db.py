import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smart_grid.db")


def init_db():
    """Create all tables if they don't already exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            from_node TEXT,
            to_node   TEXT,
            weight    INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            node      TEXT UNIQUE,
            role      TEXT,
            capacity  INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS load_balancing (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            from_node TEXT,
            to_node   TEXT,
            amount    INTEGER
        )
    """)
    conn.commit()
    conn.close()


def _ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def save_edge(from_node, to_node, weight):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO edges (timestamp, from_node, to_node, weight) VALUES (?, ?, ?, ?)",
        (_ts(), from_node, to_node, weight),
    )
    conn.commit()
    conn.close()


def save_node(node, role, capacity):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT INTO nodes (timestamp, node, role, capacity) VALUES (?, ?, ?, ?)
           ON CONFLICT(node) DO UPDATE SET
               timestamp = excluded.timestamp,
               role      = excluded.role,
               capacity  = excluded.capacity""",
        (_ts(), node, role, capacity),
    )
    conn.commit()
    conn.close()


def save_load_balancing(allocation_paths):
    conn = sqlite3.connect(DB_PATH)
    ts = _ts()
    conn.executemany(
        "INSERT INTO load_balancing (timestamp, from_node, to_node, amount) VALUES (?, ?, ?, ?)",
        [(ts, f, t, a) for f, t, a in allocation_paths],
    )
    conn.commit()
    conn.close()


def load_edges():
    """Return all edges stored in the database."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT from_node, to_node, weight FROM edges"
    ).fetchall()
    conn.close()
    return rows


def load_nodes():
    """Return latest state of every node stored in the database."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT node, role, capacity FROM nodes"
    ).fetchall()
    conn.close()
    return rows


def get_load_balancing_history(limit=50):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT timestamp, from_node, to_node, amount FROM load_balancing ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return rows


def clear_all():
    """Wipe all tables — used by 'Reset Grid' button."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM edges")
    conn.execute("DELETE FROM nodes")
    conn.execute("DELETE FROM load_balancing")
    conn.commit()
    conn.close()
