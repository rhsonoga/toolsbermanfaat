import os
import json
import tkinter as tk
from tkinter import ttk, messagebox


class CableCalculator:
    def __init__(self, parent):
        self.parent = parent
        self.window = parent.winfo_toplevel()

        self.clr_bg = "#111111"
        self.clr_accent = "#ffffff"
        self.clr_text = "#ffffff"

        self.load_data()
        self.always_on_top_var = tk.BooleanVar(value=False)
        self.setup_styles()

        self.main_frame = tk.Frame(self.parent, bg=self.clr_bg, padx=30, pady=10)
        self.main_frame.pack(fill="both", expand=True)

        self.create_widgets()
        self.update_ui_state()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "TLabel",
            background=self.clr_bg,
            font=("Ubuntu", 9),
            foreground=self.clr_text,
        )

        style.configure("Accent.TButton", font=("Ubuntu", 9, "bold"), padding=6)

        # Tombol kecil untuk "List OLT" agar tinggi lebih mirip Entry
        style.configure("Small.TButton", font=("Ubuntu", 8), padding=(6, 2))

        style.map(
            "Accent.TButton",
            background=[("active", "#E95420"), ("!disabled", self.clr_accent)],
            foreground=[("!disabled", "black")],
        )

    # ----------------------------
    # DATA / CONFIG
    # ----------------------------
    def load_data(self):
        base_dir = os.path.dirname(__file__)
        json_path = os.path.join(base_dir, "OLTdata.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except Exception:
                self.set_default_config()
        else:
            self.set_default_config()

    def set_default_config(self):
        self.config = {
            "line_names": ["MAINFEEDER CABLE", "HUBFEEDER CABLE", "SUBFEEDER CABLE"],
            "cable_types": ["FO 144C/12T", "FO 48C/4T"],
            "cable_categories": ["AE - AE Aerial"],
            "olt_codes": [],
        }

    # ----------------------------
    # OLT NOTEPAD (save near exe, fallback APPDATA)
    # ----------------------------
    def _get_exe_dir(self):
        """
        Saat dibuild jadi .exe (PyInstaller), simpan sejajar dengan exe.
        Saat run .py biasa, simpan sejajar dengan file script.
        """
        try:
            import sys

            if getattr(sys, "frozen", False):
                return os.path.dirname(sys.executable)
        except Exception:
            pass
        return os.path.dirname(__file__)

    def _get_appdata_dir(self):
        appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(appdata, "Cable Calculator")

    def _get_olt_notes_path(self):
        primary_dir = self._get_exe_dir()
        primary_path = os.path.join(primary_dir, "olt_notes.txt")

        # Coba tulis di folder exe/script dulu
        try:
            with open(primary_path, "a", encoding="utf-8") as _:
                pass
            return primary_path
        except Exception:
            # fallback ke APPDATA
            fallback_dir = self._get_appdata_dir()
            os.makedirs(fallback_dir, exist_ok=True)
            return os.path.join(fallback_dir, "olt_notes.txt")

    def load_olt_notes(self):
        path = self._get_olt_notes_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                return ""
        return ""

    def save_olt_notes(self, text):
        path = self._get_olt_notes_path()
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def open_olt_notepad(self):
        # kalau sudah terbuka, fokuskan saja
        if hasattr(self, "_olt_note_win") and self._olt_note_win.winfo_exists():
            self._olt_note_win.lift()
            self._olt_note_win.focus_force()
            return

        win = tk.Toplevel(self.window)
        self._olt_note_win = win
        win.title("List OLT Code disini, untuk masing-masing Kota")
        win.geometry("320x420")
        win.transient(self.window)

        txt = tk.Text(win, wrap="word", font=("Ubuntu", 10), bg="#F3F3F3", fg="#000000")
        txt.pack(fill="both", expand=True, padx=10, pady=10)

        txt.insert("1.0", self.load_olt_notes())

        def on_close():
            content = txt.get("1.0", "end-1c")
            try:
                self.save_olt_notes(content)
            except Exception as e:
                messagebox.showerror("Error", f"Gagal menyimpan olt_notes.txt: {e}")
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", on_close)

    # ----------------------------
    # UI
    # ----------------------------
    def create_widgets(self):
        self.name_var = tk.StringVar()
        self.route_var, self.fdt_var, self.fat_var = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self.tol_var = tk.StringVar(value="5.0")
        self.olt_var, self.code_var, self.segment_var = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self.type_var, self.cat_var = tk.StringVar(), tk.StringVar()

        input_container = tk.Frame(self.main_frame, bg=self.clr_bg)
        input_container.pack(fill="x", pady=5)

        # OLT Code dibuat khusus (Entry + Button), jadi tidak ada di fields
        fields = [
            ("Line Name:", self.name_var, "cb_name", self.config.get("line_names", [])),
            ("Cable Type:", self.type_var, "cb_type", self.config.get("cable_types", [])),
            ("Category:", self.cat_var, "cb_cat", self.config.get("cable_categories", [])),
            ("Total Route (M):", self.route_var, "ent_route", None),
            ("Slack FDT:", self.fdt_var, "ent_fdt", None),
            ("Slack FAT/SF/MF:", self.fat_var, "ent_fat", None),
            ("FDT Code:", self.code_var, "ent_code", None),
            ("Segment:", self.segment_var, "ent_seg", None),
        ]

        row = 0
        for (lbl_text, var, attr, vals) in fields:
            # Sisipkan OLT Code setelah Line Name (jadi row==1)
            if row == 1:
                ttk.Label(input_container, text="OLT Code:").grid(row=row, column=0, sticky="w", pady=4)

                olt_frame = tk.Frame(input_container, bg=self.clr_bg)
                olt_frame.grid(row=row, column=1, padx=15, pady=4, sticky="w")

                self.ent_olt = ttk.Entry(olt_frame, textvariable=self.olt_var, width=36)
                self.ent_olt.pack(side="left")

                self.btn_olt_list = ttk.Button(
                    olt_frame,
                    text="List OLT",
                    command=self.open_olt_notepad,
                    style="Small.TButton",
                )
                self.btn_olt_list.pack(side="left", padx=(8, 0))

                row += 1

            ttk.Label(input_container, text=lbl_text).grid(row=row, column=0, sticky="w", pady=4)
            if vals is not None:
                widget = ttk.Combobox(
                    input_container,
                    textvariable=var,
                    width=45,
                    state="readonly",
                    values=vals,
                )
            else:
                widget = ttk.Entry(input_container, textvariable=var, width=48)

            widget.grid(row=row, column=1, padx=15, pady=4, sticky="w")
            setattr(self, attr, widget)
            row += 1

        self.name_var.trace_add("write", self.update_ui_state)

        btn_frame = tk.Frame(self.main_frame, bg=self.clr_bg)
        btn_frame.pack(fill="x", pady=15)
        self.btn_generate = ttk.Button(
            btn_frame, text="GENERATE REPORT", style="Accent.TButton", command=self.calculate
        )
        self.btn_generate.pack(side="left", padx=(0, 10))
        ttk.Button(btn_frame, text="CLEAR", command=self.clear_fields).pack(side="left")

        ttk.Checkbutton(
            self.main_frame,
            text="Toggle on Top",
            variable=self.always_on_top_var,
            command=self.toggle_on_top,
        ).pack(anchor="w")

        tk.Label(
            self.main_frame,
            text="Calculated:",
            bg=self.clr_bg,
            fg=self.clr_accent,
            font=("Ubuntu", 9, "bold"),
        ).pack(anchor="w", pady=(15, 5))

        self.output_text = tk.Text(
            self.main_frame,
            font=("Ubuntu", 10),
            bg="#252525",
            fg="#fcfcfc",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#252525",
            padx=10,
            pady=10,
            height=10,
            width=80,
        )
        self.output_text.pack(anchor="w")

        for v in [
            self.route_var,
            self.fdt_var,
            self.fat_var,
            self.olt_var,
            self.code_var,
            self.segment_var,
            self.type_var,
        ]:
            v.trace_add("write", lambda *args: self.validate_inputs())

    def toggle_on_top(self):
        self.window.attributes("-topmost", self.always_on_top_var.get())

    def clear_fields(self):
        for v in [
            self.route_var,
            self.fdt_var,
            self.fat_var,
            self.olt_var,
            self.code_var,
            self.name_var,
            self.type_var,
            self.cat_var,
            self.segment_var,
        ]:
            v.set("")
        self.tol_var.set("5.0")
        self.output_text.delete("1.0", tk.END)

    def update_ui_state(self, *args):
        mode = self.name_var.get()

        # OLT sekarang Entry, jadi state default "normal" (bukan readonly)
        states = {"fdt": "normal", "fat": "normal", "olt": "normal", "code": "normal", "seg": "normal"}

        if "MAINFEEDER" in mode or "HUBFEEDER" in mode:
            states["fdt"], states["code"] = "disabled", "disabled"
            self.fdt_var.set("0")
            self.code_var.set("")
        elif "SUBFEEDER" in mode:
            states["seg"] = "disabled"
            self.segment_var.set("")
        elif any(x in mode for x in ["LINE A", "LINE B", "LINE C", "LINE D"]):
            states["olt"], states["seg"] = "disabled", "disabled"
            self.olt_var.set("")
            self.segment_var.set("")

        self.ent_fdt.config(state=states["fdt"])
        self.ent_fat.config(state=states["fat"])

        # OLT Entry + tombol ikut state
        self.ent_olt.config(state=states["olt"])
        self.btn_olt_list.config(state=("disabled" if states["olt"] == "disabled" else "normal"))

        self.ent_code.config(state=states["code"])
        self.ent_seg.config(state=states["seg"])

        self.validate_inputs()

    def validate_inputs(self, *args):
        mode = self.name_var.get()
        if not mode:
            self.btn_generate.state(["disabled"])
            return

        req = [self.route_var.get(), self.fat_var.get(), self.type_var.get()]
        if "SUBFEEDER" in mode:
            req.extend([self.fdt_var.get(), self.code_var.get(), self.olt_var.get()])
        elif "MAINFEEDER" in mode or "HUBFEEDER" in mode:
            req.extend([self.olt_var.get(), self.segment_var.get()])
        elif "LINE" in mode:
            req.extend([self.fdt_var.get(), self.code_var.get()])

        self.btn_generate.state(["!disabled"] if all(req) else ["disabled"])

    def calculate(self):
        try:
            r = float(self.route_var.get() or 0)
            fdt = int(self.fdt_var.get() or 0)
            fat = int(self.fat_var.get() or 0)
            tol = float(self.tol_var.get())

            total_unit = fdt + fat
            slack_m = total_unit * 20
            base = r + slack_m
            final = round(base + (base * (tol / 100)))

            cat = self.cat_var.get().split(" - ")[0]
            olt = self.olt_var.get().strip()  # OLT bebas, tidak di-split lagi
            seg = self.segment_var.get()
            code = self.code_var.get()
            line_name = self.name_var.get()

            report = (
                f"Total Route = {int(r)} M\n"
                f"Total Slack = {total_unit} unit ({fdt} slack FDT & {fat} slack FAT/SF/MF) @20M\n"
                f"Toleransi = {int(tol)}%\n"
                f"Total Length Cable = {int(r)}+{slack_m} = {int(base)}M + ({int(base)} x {int(tol)}%) = {final} M\n"
                f"{'—' * 75}\n"
            )

            if "SUBFEEDER" in line_name:
                report += f"{olt} - {code} - {line_name} ({self.type_var.get()}) - {cat} - {final} M"
            elif "LINE" in line_name:
                report += f"{code} - {line_name} ({self.type_var.get()}) - {cat} - {final} M"
            else:
                report += f"{olt} - {line_name} {seg} ({self.type_var.get()}) - {cat} - {final} M"

            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", report)

        except Exception as e:
            messagebox.showerror("Error", f"Input not valid: {str(e)}")