import os
import json
import sys
import tkinter as tk
from qris import DonationGate
from hwid_utils import get_machine_id, generate_verification_key

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FTTH CONVERTER TOOLS")
        self.geometry("900x820")
        self.minsize(900, 820)

        # Path aman untuk icon (supaya tidak error saat jadi .exe)
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, "app.ico")
        else:
            icon_path = os.path.join(os.path.dirname(__file__), "app.ico")
            
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        self.active_button = None
        self.configure(bg="#300A24") 

        # Konfigurasi Tema
        self.bg_sidebar = "#300A24" 
        self.bg_btn = "#3D3C3D"     
        self.fg_color = "#E95420"   
        self.fg_white = "#FFFFFF"   
        self.font_title = ("Ubuntu", 16, "bold")
        self.font_main = ("Ubuntu", 12, "bold")

        if not self.check_activation():
            self.withdraw()
            DonationGate(self, self.start_application)
        else:
            self.start_application()

    def check_activation(self):
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    data = json.load(f)
                    user_key = data.get("user_id", "")
                    if not user_key or user_key == "null": return False
                    
                    machine_id = get_machine_id()
                    return user_key == generate_verification_key(machine_id)
            return False
        except: return False

    def start_application(self):
        self.deiconify()
        self.setup_ui()
        self.load_custom_scripts()

    def setup_ui(self):
        # --- SIDEBAR ---
        self.sidebar = tk.Frame(self, bg=self.bg_sidebar, width=240)
        self.sidebar.pack(side="left", fill="y", padx=(5, 2), pady=5)
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="CONVERTER V2.0", bg=self.bg_sidebar, 
                 fg=self.fg_color, font=self.font_title, anchor="w").pack(fill="x", padx=15, pady=20)

        self.menus = ["Cable_Calculator", "HPDB_Converter", "BOQ_Converter"]
        self.buttons = {} 
        
        for menu in self.menus:
            btn = tk.Label(self.sidebar, text=f"  {menu}", bg=self.bg_btn, fg=self.fg_white, 
                           font=self.font_main, anchor="w", pady=8, cursor="hand2")
            btn.pack(fill="x", padx=15, pady=8)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#E95420"))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=self.bg_btn) if b != self.active_button else None)
            self.buttons[menu] = btn 

        # --- MAIN AREA ---
        self.main_area = tk.Frame(self, bg="#111111")
        self.main_area.pack(side="right", fill="both", expand=True, padx=(2, 5), pady=5)

        self.lbl_welcome = tk.Label(self.main_area, text="Hanya berusaha mempermudah pekerjaanmu... ^_^", 
                                    bg="#111111", fg=self.fg_white, font=self.font_title, anchor="w")
        self.lbl_welcome.pack(fill="x", padx=20, pady=20)

    def set_active_visual(self, clicked_btn):
        for btn in self.buttons.values():
            btn.configure(bg=self.bg_btn)
        self.active_button = clicked_btn
        self.active_button.configure(bg="#E95420")

    def clear_main_area(self):
        for widget in self.main_area.winfo_children():
            widget.destroy()

    def load_custom_scripts(self):
        self.buttons["Cable_Calculator"].bind("<Button-1>", self.open_cable_calculator)
        self.buttons["HPDB_Converter"].bind("<Button-1>", self.open_hpdb_converter)
        self.buttons["BOQ_Converter"].bind("<Button-1>", self.open_boq_converter)

    # --- KUNCI OPTIMASI: LAZY LOADING ---

    def open_cable_calculator(self, event=None):
        self.set_active_visual(self.buttons["Cable_Calculator"])
        self.clear_main_area()
        # Modul ringan, tapi tetap kita panggil secara lazy
        from cable_calculator.mainapp import CableCalculator
        CableCalculator(self.main_area)

    def open_hpdb_converter(self, event=None):
        self.set_active_visual(self.buttons["HPDB_Converter"])
        self.clear_main_area()
        # Import ditaruh di sini agar library Pandas tidak dimuat saat startup
        from hpdb_converter.gui_hpdb import HPDBConverter
        HPDBConverter(self.main_area)

    def open_boq_converter(self, event=None):
        self.set_active_visual(self.buttons["BOQ_Converter"])
        self.clear_main_area()
        # Import ditaruh di sini agar library Openpyxl tidak dimuat saat startup
        from boq_converter.gui_boq import BOMAutomationGUI
        BOMAutomationGUI(self.main_area)

if __name__ == "__main__":
    app = Launcher()
    app.mainloop()