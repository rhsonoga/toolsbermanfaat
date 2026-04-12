import os
from .core.parser import parse_kmz           # Tambah titik
from .core.aggregator import aggregate_kml_structure # Tambah titik
from .exporter.excel_writer import export_to_excel   # Tambah titik
from .bom_input import run_injection         # Tambah titik

def convert(kmz_path, output_name=None, mode="CLUSTER"):
    """
    Fungsi Utama Konversi BOQ
    REVISI: Penanganan path assets secara dinamis (Backend Template)
    """
    
    # 1. Tentukan Path Folder Assets secara internal di dalam modul boq_converter
    base_dir = os.path.dirname(__file__)
    assets_dir = os.path.join(base_dir, "assets")

    # 2. Penentuan Nama File Output & Template Backend
    # Mode diseragamkan ke Upper Case untuk menghindari typo
    current_mode = mode.upper()

    if current_mode == "CLUSTER":
        mid_output = "1.CLUSTER_KONVERSI.xlsx"
        final_output = "2.BOQ_CLUSTER.xlsx"
        template_name = "cluster.xlsx"
    elif current_mode == "FEEDER":
        mid_output = "1.FEEDER_KONVERSI.xlsx"
        final_output = "2.BOQ_FEEDER.xlsx"
        template_name = "feeder.xlsx"
    else:
        # Menangani mode tambahan atau error mode
        mid_output = f"1.{current_mode}_KONVERSI.xlsx"
        final_output = f"2.BOQ_{current_mode}.xlsx"
        template_name = "feeder.xlsx" # Default fallback ke feeder jika mode asing

    template_path = os.path.join(assets_dir, template_name)

    # Validasi keberadaan template di backend sebelum proses berat dimulai
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"❌ Template {template_name} tidak ditemukan di folder backend: {assets_dir}")

    # --- LANGKAH 1: KONVERSI (KMZ ke File Sementara 1) ---
    print(f"[{current_mode}] Memulai Parsing KMZ...")
    structure = parse_kmz(kmz_path)

    print(f"[{current_mode}] Mengagregasi data struktur KML...")
    project_data = aggregate_kml_structure(structure, mode=current_mode)

    print(f"[{current_mode}] Membuat file konversi sementara: {mid_output}")
    export_to_excel(project_data, mid_output, mode=current_mode)

    # --- LANGKAH 2: INJEKSI (File 1 ke Template BOQ Final) ---
    print(f"[{current_mode}] Memulai Injeksi data ke Template Backend...")
    # Template dibaca dari backend (assets), hasil disimpan ke root agar bisa di-download GUI
    run_injection(template_path, mid_output, final_output, mode=current_mode)

    print(f"\n✅ PROSES SELESAI!")
    print(f"1. File Konversi: {mid_output}")
    print(f"2. File BOQ Final: {final_output}")
    
    return mid_output, final_output

if __name__ == "__main__":
    # Fungsi main hanya untuk testing mandiri (CLI)
    print("=== KMZ TO BOQ SYSTEM (DEBUG MODE) ===")
    kmz_file = input("Masukkan path file KMZ: ")
    project_mode = input("Pilih Mode (CLUSTER/FEEDER): ").upper() or "CLUSTER"
    
    if os.path.exists(kmz_file):
        try:
            convert(kmz_file, mode=project_mode)
        except Exception as e:
            print(f"Terjadi Kesalahan: {e}")
    else:
        print("File KMZ tidak ditemukan.")