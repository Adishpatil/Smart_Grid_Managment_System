import tkinter as tk
from gui import SmartGridVisualizer
 
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Smart Grid Management System")
    root.geometry("1150x760")
    root.minsize(900, 600)
    SmartGridVisualizer(root)
    root.mainloop()
 