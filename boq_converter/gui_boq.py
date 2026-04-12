import tkinter as tk
from tkinter import filedialog, messagebox
import os
import shutil

# PENTING: Menggunakan relative import (tanda titik) agar dikenali oleh launcher.py
try:
    from .main import convert
except ImportError as e:
    # Fallback untuk running mandiri (debug)
    try:
        from main import convert
    except:
        print(f"Error: System files missing! {e}")

class BOMAutomationGUI:
    def __init__(self, parent):
        self.parent = parent 
        
        # --- KONFIGURASI VISUAL UBUNTU (Yaru Style) ---
        self.bg_main = "#111111"      
        self.accent_color = "#E95420" 
        self.bg_btn = "#3D3C3D"       
        self.bg_dl = "#2E7D32"        # Hijau untuk Download
        self.fg_white = "#FFFFFF"
        self.font_title = ("Ubuntu", 14, "bold")
        self.font_label = ("Ubuntu", 10, "bold")
        self.font_log = ("Ubuntu Mono", 9)

        # Variables untuk melacak file hasil agar bisa di-download
        self.kmz_path = tk.StringVar()
        self.last_mid_output = ""
        self.last_final_output = ""

        self.setup_ui()

    def setup_ui(self):
        # Container Utama
        self.main_container = tk.Frame(self.parent, bg=self.bg_main, padx=20, pady=20)
        self.main_container.pack(fill="both", expand=True)

        # Header
        tk.Label(self.main_container, text="KMZ to BoQ CONVERTER SYSTEM", 
                 font=self.font_title, bg=self.bg_main, fg=self.accent_color).pack(anchor="w", pady=(0, 15))

        # --- INPUT SECTION ---
        frame_kmz = tk.LabelFrame(self.main_container, text=" SOURCE KMZ : ", 
                                  bg=self.bg_main, fg=self.fg_white, font=self.font_label,
                                  padx=10, pady=10, relief="flat", highlightthickness=1, highlightbackground="#3D3C3D")
        frame_kmz.pack(fill="x", pady=5)
        
        tk.Entry(frame_kmz, textvariable=self.kmz_path, bg="#FFFFFF", borderwidth=0).pack(side="left", fill="x", expand=True, padx=(0, 5), ipady=3)
        
        btn_browse = tk.Button(frame_kmz, text="Browse", command=self.browse_kmz, 
                               bg=self.bg_btn, fg=self.fg_white, relief="flat", cursor="hand2", padx=15)
        btn_browse.pack(side="right")

        # --- PROCESS BUTTONS ---
        process_frame = tk.Frame(self.main_container, bg=self.bg_main)
        process_frame.pack(fill="x", pady=15)

        def create_proc_btn(parent, text, cmd, color):
            btn = tk.Button(parent, text=text, command=cmd, bg=color, fg=self.fg_white,
                            font=self.font_label, height=2, relief="flat", cursor="hand2")
            btn.bind("<Enter>", lambda e: btn.configure(bg=self.accent_color))
            btn.bind("<Leave>", lambda e: btn.configure(bg=color))
            return btn

        self.btn_cluster = create_proc_btn(process_frame, "PROSES CLUSTER", lambda: self.start_automation("CLUSTER"), "#3D3C3D")
        self.btn_cluster.pack(side="left", fill="x", expand=True, padx=2)

        self.btn_feeder = create_proc_btn(process_frame, "PROSES FEEDER", lambda: self.start_automation("FEEDER"), "#3D3C3D")
        self.btn_feeder.pack(side="left", fill="x", expand=True, padx=2)

        # --- LOG BOX (20 BARIS PAS) ---
        log_header = tk.Frame(self.main_container, bg=self.bg_main)
        log_header.pack(fill="x", pady=(10, 0))
        tk.Label(log_header, text="Log Report :", font=self.font_label, bg=self.bg_main, fg=self.fg_white).pack(side="left")
        
        tk.Button(log_header, text="RESET", command=self.reset_form, 
                  bg="#CE0000", fg=self.fg_white, relief="flat", padx=10).pack(side="right")

        self.log_area = tk.Text(self.main_container, height=10, width=50, 
                                font=self.font_log, bg="#1A1A1A", fg="#00FF00", 
                                relief="flat", highlightthickness=1, highlightbackground="#3D3C3D")
        self.log_area.pack(fill="x", expand=False, pady=5)
        self.log_area.config(state="disabled")

        # --- DOWNLOAD SECTION (DI BAWAH LOG BOX) ---
        dl_frame = tk.Frame(self.main_container, bg=self.bg_main)
        dl_frame.pack(fill="x", pady=10)

        self.btn_dl_mid = tk.Button(dl_frame, text="Download Hasil Konversi", command=self.download_mid,
                                   bg=self.bg_dl, fg=self.fg_white, font=self.font_label, relief="flat", cursor="hand2", pady=8)
        self.btn_dl_mid.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.btn_dl_final = tk.Button(dl_frame, text="Download BOQ Final", command=self.download_final,
                                     bg=self.bg_dl, fg=self.fg_white, font=self.font_label, relief="flat", cursor="hand2", pady=8)
        self.btn_dl_final.pack(side="left", fill="x", expand=True, padx=(5, 0))

    # ================= LOGIC & DOWNLOAD =================
    def write_log(self, text):
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, f"> {text}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state="disabled")
        self.parent.update()

    def browse_kmz(self):
        filename = filedialog.askopenfilename(filetypes=[("KMZ files", "*.kmz")])
        if filename: self.kmz_path.set(filename)

    def reset_form(self):
        self.kmz_path.set("")
        self.log_area.config(state="normal")
        self.log_area.delete('1.0', tk.END)
        self.log_area.config(state="disabled")
        self.write_log("System Ready. Pilih file KMZ.")

    def download_mid(self):
        if not self.last_mid_output or not os.path.exists(self.last_mid_output):
            return messagebox.showwarning("File Missing", "Jalankan proses terlebih dahulu!")
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=self.last_mid_output, filetypes=[("Excel", "*.xlsx")])
        if path:
            shutil.copy(self.last_mid_output, path)
            self.write_log(f"💾 File Konversi disimpan: {os.path.basename(path)}")

    def download_final(self):
        if not self.last_final_output or not os.path.exists(self.last_final_output):
            return messagebox.showwarning("File Missing", "Selesaikan proses konversi & injeksi!")
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=self.last_final_output, filetypes=[("Excel", "*.xlsx")])
        if path:
            shutil.copy(self.last_final_output, path)
            self.write_log(f"💾 BOQ Final disimpan: {os.path.basename(path)}")

    def start_automation(self, mode):
        kmz = self.kmz_path.get()
        if not kmz:
            messagebox.showwarning("Peringatan", "Harap pilih file KMZ!")
            return

        # Mapping file untuk kebutuhan download
        config = {
            "CLUSTER": {"mid": "1.CLUSTER_KONVERSI.xlsx", "final": "2.BOQ_CLUSTER.xlsx"},
            "FEEDER": {"mid": "1.FEEDER_KONVERSI.xlsx", "final": "2.BOQ_FEEDER.xlsx"}
        }
        
        # Simpan nama file ke variabel class agar bisa di-copy saat tombol download diklik
        self.last_mid_output = config[mode.upper()]["mid"]
        self.last_final_output = config[mode.upper()]["final"]

        try:
            self.log_area.config(state="normal")
            self.log_area.delete('1.0', tk.END)
            self.log_area.config(state="disabled")
            
            self.write_log(f"MODE AKTIF: {mode.upper()}")
            self.write_log(f"Sedang memproses... mohon tunggu.")

            # Pastikan memanggil convert dengan mode.upper()
            convert(kmz, mode=mode.upper())

            self.write_log(f"✅ PROSES {mode.upper()} BERHASIL!")
            self.write_log(f"Silakan klik tombol Download di bawah.")
            messagebox.showinfo("Sukses", f"Konversi {mode} Selesai!")

        except Exception as e:
            self.write_log(f"❌ ERROR: {str(e)}")
            messagebox.showerror("System Error", str(e))