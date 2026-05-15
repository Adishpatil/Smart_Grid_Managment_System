import ttkbootstrap as tb
from gui import SmartGridVisualizer

if __name__ == "__main__":
    # Use ttkbootstrap for a modern, flat UI
    root = tb.Window(themename="darkly")
    root.title("Smart City Energy Grid Management System")
    root.geometry("1200x800")
    root.minsize(1000, 700)
    app = SmartGridVisualizer(root)
    root.mainloop()