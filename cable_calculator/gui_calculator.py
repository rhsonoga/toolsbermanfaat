import tkinter as tk
from mainapp import CableCalculator


class Launcher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Cable Calculator")
        self.root.minsize(950, 550)

        self.start_main_app()
        self.root.mainloop()

    def start_main_app(self):
        """Memuat Kalkulator Utama"""
        for widget in self.root.winfo_children():
            widget.destroy()

        self.app = CableCalculator(self.root)


if __name__ == "__main__":
    Launcher()