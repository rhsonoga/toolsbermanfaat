import tkinter as tk
from tkinter import filedialog, messagebox
import os
import shutil
# Import disesuaikan dengan struktur folder
from .session_engine import SessionEngine

class HPDBConverter:
    def __init__(self, parent):
        self.parent = parent 

        # ================= VARIABLES =================
        self.kmz_path = tk.StringVar()
        self.hpdb_path = tk.StringVar()
        self.cache_data = None
        self.session = None

        # --- KONFIGURASI VISUAL UBUNTU ---
        self.bg_main = "#111111"      # Gelap (Main Area Launcher)
        self.bg_sidebar = "#300A24"   # Aubergine
        self.accent_color = "#E95420" # Ubuntu Orange
        self.bg_btn = "#3D3C3D"       # Dark Grey Button
        self.fg_white = "#FFFFFF"
        
        self.font_title = ("Ubuntu", 14, "bold")
        self.font_label = ("Ubuntu", 10, "bold")
        self.font_log = ("Ubuntu Mono", 9)

        self.setup_ui()

    def setup_ui(self):
        # Container utama menyesuaikan background main_area launcher
        self.main_container = tk.Frame(self.parent, bg=self.bg_main, padx=20, pady=20)
        self.main_container.pack(fill="both", expand=True)

        # Header Title
        header_label = tk.Label(
            self.main_container, 
            text="HPDB INJECTOR SYSTEM", 
            font=self.font_title,
            bg=self.bg_main,
            fg=self.accent_color
        )
        header_label.pack(anchor="w", pady=(0, 15))

        # --- TAHAP 1: SOURCE SELECTION ---
        group1 = tk.LabelFrame(self.main_container, 
                               bg=self.bg_main, fg=self.fg_white, font=self.font_label, 
                               padx=10, pady=10, relief="flat", highlightthickness=1, highlightbackground="#3D3C3D")
        group1.pack(fill="x", pady=5)

        tk.Label(group1, text="SOURCE KMZ :", bg=self.bg_main, fg=self.fg_white, font=self.font_label).pack(anchor="w")
        f1 = tk.Frame(group1, bg=self.bg_main)
        f1.pack(pady=5, fill="x")
        
        tk.Entry(f1, textvariable=self.kmz_path, bg="#FFFFFF", fg="#000000", borderwidth=0).pack(side="left", fill="x", expand=True, padx=(0, 5), ipady=3)
        
        btn_browse1 = tk.Button(f1, text="Browse", command=self.browse_kmz, bg=self.bg_btn, fg=self.fg_white, 
                                relief="flat", cursor="hand2", padx=10)
        btn_browse1.pack(side="right")
        btn_browse1.bind("<Enter>", lambda e: btn_browse1.configure(bg=self.accent_color))
        btn_browse1.bind("<Leave>", lambda e: btn_browse1.configure(bg=self.bg_btn))

        # --- ACTION BUTTONS ---
        btn_frame = tk.Frame(self.main_container, bg=self.bg_main)
        btn_frame.pack(fill="x", pady=10)

        # Helper untuk membuat tombol step yang seragam
        def create_step_btn(parent, text, command):
            btn = tk.Button(parent, text=text, command=command, bg=self.bg_btn, fg=self.fg_white, 
                            font=self.font_label, relief="flat", pady=8, cursor="hand2")
            btn.pack(fill="x", pady=2)
            btn.bind("<Enter>", lambda e: btn.configure(bg=self.accent_color))
            btn.bind("<Leave>", lambda e: btn.configure(bg=self.bg_btn))
            return btn

        self.btn_s1 = create_step_btn(btn_frame, "STEP 1: CONVERTING KMZ", self.do_step1)
        self.btn_s2 = create_step_btn(btn_frame, "STEP 2: INJECT TO HPDB (BASIC)", self.do_step2)

        # --- TAHAP 3: SYNCHRONIZATION ---
        group2 = tk.LabelFrame(self.main_container, text=" Synchronization ", 
                               bg=self.bg_main, fg=self.fg_white, font=self.font_label, 
                               padx=10, pady=10, relief="flat", highlightthickness=1, highlightbackground="#3D3C3D")
        group2.pack(fill="x", pady=10)

        tk.Label(group2, text="Basic file (path jangan di edit)", bg=self.bg_main, fg=self.fg_white, font=self.font_label).pack(anchor="w")
        f2 = tk.Frame(group2, bg=self.bg_main)
        f2.pack(pady=5, fill="x")
        
        tk.Entry(f2, textvariable=self.hpdb_path, bg="#FFFFFF", fg="#000000", borderwidth=0).pack(side="left", fill="x", expand=True, padx=(0, 5), ipady=3)
        
        btn_browse2 = tk.Button(f2, text="Browse", command=self.browse_hpdb, bg=self.bg_btn, fg=self.fg_white, 
                                relief="flat", cursor="hand2", padx=10)
        
        btn_browse2.bind("<Enter>", lambda e: btn_browse2.configure(bg=self.accent_color))
        btn_browse2.bind("<Leave>", lambda e: btn_browse2.configure(bg=self.bg_btn))

        self.btn_s3 = create_step_btn(self.main_container, "STEP 3: SYNC KOLOM A-K (FINAL)", self.do_step3)

        # --- LOG BOX ---
        log_header = tk.Frame(self.main_container, bg=self.bg_main)
        log_header.pack(fill="x", pady=(10, 0))
        tk.Label(log_header, text="Log Report :", font=self.font_label, bg=self.bg_main, fg=self.fg_white).pack(side="left")
        
        btn_reset = tk.Button(log_header, text="RESET", width=8, command=self.reset_session, bg="#C70505", fg=self.fg_white, relief="flat")
        btn_reset.pack(side="right")

        self.log = tk.Text(
            self.main_container, 
            height=9,
            width=50, 
            font=self.font_log, 
            bg="#252525", 
            fg="#FFFFFF", # Terminal
            relief="flat",
            highlightthickness=1,
            highlightbackground="#3D3C3D"
        )
        self.log.pack(fill="x", expand=False, pady=5)
        self.log.config(state="disabled")

    # --- DOWNLOAD BUTTONS (DI BAWAH LOG BOX) ---
        dl_frame = tk.Frame(self.main_container, bg=self.bg_main)
        dl_frame.pack(fill="x", pady=10)

        # Tombol Download S1
        self.btn_dl1 = tk.Button(dl_frame, text="Download Hasil Konversi", command=self.download_s1, 
                                bg="#2E7D32", fg=self.fg_white, font=self.font_label, relief="flat", cursor="hand2", pady=5)
        self.btn_dl1.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # Tombol Download S2 (Final)
        self.btn_dl2 = tk.Button(dl_frame, text="Download Final HPDB", command=self.download_s2, 
                                bg="#2E7D32", fg=self.fg_white, font=self.font_label, relief="flat", cursor="hand2", pady=5)
        self.btn_dl2.pack(side="left", fill="x", expand=True, padx=(5, 0))    

    # ================= LOGIC (UNCHANGED) =================
    def write_log(self, msg):
        self.log.config(state="normal")
        self.log.insert("end", f"> {msg}\n")
        self.log.see("end")
        self.log.config(state="disabled")
        self.parent.update()

    def reset_session(self):
        self.session = None
        self.cache_data = None
        self.kmz_path.set("")
        self.hpdb_path.set("")
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")
        self.write_log("🔄 Session di-reset.")

    def download_s1(self):
        source = "1.Hasil_Convert.xlsx"
        if not os.path.exists(source):
            return messagebox.showwarning("File Missing", "Jalankan Step 1 terlebih dahulu!")
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile="1.Hasil_Convert.xlsx",
            filetypes=[("Excel Files", "*.xlsx")]
        )
        if save_path:
            shutil.copy(source, save_path)
            self.write_log(f"💾 File S1 berhasil disimpan ke: {save_path}")

    def download_s2(self):
        source = "2.HPDB_FINAL.xlsx"
        if not os.path.exists(source):
            return messagebox.showwarning("File Missing", "Jalankan Step 2 & 3 terlebih dahulu!")
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile="2.HPDB_FINAL.xlsx",
            filetypes=[("Excel Files", "*.xlsx")]
        )
        if save_path:
            shutil.copy(source, save_path)
            self.write_log(f"💾 File Final HPDB berhasil disimpan ke: {save_path}")

    def browse_kmz(self):
        path = filedialog.askopenfilename(filetypes=[("KMZ Files", "*.kmz")])
        if path: self.kmz_path.set(path)

    def browse_hpdb(self):
        path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
        if path: self.hpdb_path.set(path)

    def do_step1(self):
        try:
            if not self.kmz_path.get():
                return messagebox.showwarning("Error", "Pilih file KMZ!")
            self.write_log("Tahap 1: Mengonversi KMZ...")
            self.session = SessionEngine(self.kmz_path.get())
            self.cache_data = self.session.step1_convert()
            self.write_log("✅ Tahap 1 Selesai!")
        except Exception as e:
            self.write_log(f"Error S1: {e}")

    def do_step2(self):
        try:
            if not self.session:
                return messagebox.showwarning("Error", "Jalankan Tahap 1 dulu!")
            self.write_log("Tahap 2: Injeksi data dasar...")
            out = self.session.step2_inject_basic()
            self.hpdb_path.set(os.path.abspath(out))
            self.write_log(f"✅ Tahap 2 Selesai! File: {out}")
        except Exception as e:
            self.write_log(f"Error S2: {e}")

    def do_step3(self):
        try:
            if not self.session:
                return messagebox.showwarning("Error", "Jalankan Tahap 1 & 2 dulu!")
            self.write_log("Tahap 3: Sinkronisasi Kolom A-K...")
            self.session.step3_sync_pole()
            self.write_log("✅ Tahap 3 Selesai!")
            messagebox.showinfo("Success", "Semua tahapan selesai!")
        except Exception as e:
            self.write_log(f"Error S3: {e}")