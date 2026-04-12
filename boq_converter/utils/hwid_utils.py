import subprocess
import hashlib

def get_machine_id():
    """Mengambil ID unik hardware (Serial Number Motherboard)"""
    try:
        # Mengambil serial number motherboard menggunakan WMIC
        cmd = "wmic baseboard get serialnumber"
        serial = subprocess.check_output(cmd, shell=True).decode().split('\n')[1].strip()
        
        # Jika serial kosong atau gagal, gunakan Disk Drive serial sebagai cadangan
        if not serial or "None" in serial:
            cmd = "wmic diskdrive get serialnumber"
            serial = subprocess.check_output(cmd, shell=True).decode().split('\n')[1].strip()
            
        return serial
    except:
        # Fallback terakhir jika semua perintah WMIC gagal
        return "DEV-MACHINE-99"

def generate_verification_key(machine_id):
    """Fungsi verifikasi: Mencocokkan ID + Salt dengan Hash SHA-256"""
    # SALT RAHASIA (Jangan diberikan ke siapa-siapa!)
    secret_salt = "kopi_hitam_2026" 
    
    raw_key = machine_id + secret_salt
    hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
    
    return hashed_key.upper()