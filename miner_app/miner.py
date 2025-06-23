# управление майнером (запуск, стоп, батники)
import os
import subprocess
import zipfile

def unzip_trex(zip_name="t-rex-0.26.8-win.zip"):
    extract_path = os.path.join(os.getcwd(), "Miner")
    trex_path = os.path.join(extract_path, "t-rex.exe")
    if not os.path.exists(trex_path):
        with zipfile.ZipFile(zip_name, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
    return trex_path

def start_miner(trex_path, algo, pool, wallet, worker="MyWorker"):
    cmd = [trex_path, "-a", algo, "-o", pool, "-u", f"{wallet}.{worker}", "-p", "x"]
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
