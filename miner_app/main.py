import os
import sys
import zipfile
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image
import psutil
from py3nvml import py3nvml
import keyboard
import pystray
import requests

class MinerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Miner Controller")
        self.geometry("400x300")
        self.icon_image = None
        self.miner_process = None

        self.create_widgets()

        try:
            py3nvml.nvmlInit()
        except:
            messagebox.showwarning("Внимание", "Не удалось инициализировать NVML. GPU-статистика не доступна.")

        self.start_mining()
        self.update_stats()
        self.update_balance()

        keyboard.add_hotkey('w', self.stop_mining)
        self.create_tray_icon()

    def create_widgets(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TLabel", font=("Segoe UI", 12))
        style.configure("Stat.TLabel", font=("Segoe UI", 14, "bold"))

        self.cpu_label = ttk.Label(self, text="CPU Usage: ", style="Stat.TLabel")
        self.cpu_label.pack(pady=5)

        self.ram_label = ttk.Label(self, text="RAM Usage: ", style="Stat.TLabel")
        self.ram_label.pack(pady=5)

        self.gpu_label = ttk.Label(self, text="GPU Usage: ", style="Stat.TLabel")
        self.gpu_label.pack(pady=5)

        self.balance_label = ttk.Label(self, text="Balance: loading...", foreground="blue", style="Stat.TLabel")
        self.balance_label.pack(pady=5)

        self.workers_label = ttk.Label(self, text="Workers: loading...", foreground="blue", style="Stat.TLabel")
        self.workers_label.pack(pady=5)

        self.status_label = ttk.Label(self, text="Miner status: Starting...", foreground="green", style="Stat.TLabel")
        self.status_label.pack(pady=10)

        self.instruction_label = ttk.Label(self, text="Press 'W' to stop the miner.", font=("Segoe UI", 10, "italic"))
        self.instruction_label.pack(side="bottom", pady=5)

    def save_bat_file(self, filename, algo, pool, wallet, worker="MyWorker"):
        try:
            os.makedirs("Miner", exist_ok=True)
            path = os.path.join("Miner", filename)
            with open(path, "w") as f:
                f.write(f"t-rex.exe -a {algo} -o {pool} -u {wallet}.{worker} -p x")
        except Exception as e:
            print(f"Ошибка записи батника {filename}: {e}")

    def detect_mining_params(self):
        def edit_bat_file(filename, wallet, worker="MyWorker"):
            path = os.path.join("Miner", filename)
            try:
                with open(path, "r") as f:
                    lines = f.readlines()

                with open(path, "w") as f:
                    for line in lines:
                        if "-u" in line:
                            parts = line.split()
                            new_line = ""
                            for i, part in enumerate(parts):
                                if part == "-u" and i + 1 < len(parts):
                                    parts[i + 1] = f"{wallet}.{worker}"
                                    break
                            new_line = " ".join(parts)
                            f.write(new_line + "\n")
                        else:
                            f.write(line)
            except Exception as e:
                print(f"Ошибка при редактировании {filename}: {e}")

        try:
            handle = py3nvml.nvmlDeviceGetHandleByIndex(0)
            mem_info = py3nvml.nvmlDeviceGetMemoryInfo(handle)
            mem_gb = mem_info.total / (1024 ** 3)
        except Exception:
            mem_gb = 0

        if mem_gb >= 5.2:
            algo = "kawpow"
            pool = "stratum+tcp://rvn.2miners.com:6060"
            wallet = "RB5UYWXZBgXUFTA5HeuEa5e7jCf8dSER9n"
            edit_bat_file("RVN-2miners.bat", wallet)

        elif mem_gb >= 3.5:
            algo = "ethash"
            pool = "stratum+tcp://ethash.poolbinance.com:1800"
            wallet = "0x090044c81D598A00a1AcE61E73895ef3b8aCdBA8"
            edit_bat_file("ETC-2miners.bat", wallet)

        else:
            algo = ""
            pool = ""
            wallet = ""

        return algo, pool, wallet

    def update_stats(self):
        cpu_percent = psutil.cpu_percent(interval=1)
        self.cpu_label.config(text=f"CPU Usage: {cpu_percent}%")

        ram = psutil.virtual_memory()
        self.ram_label.config(text=f"RAM Usage: {ram.percent}%")

        gpu_text = "GPU Usage: N/A"
        try:
            handle = py3nvml.nvmlDeviceGetHandleByIndex(0)
            util = py3nvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_text = f"GPU Usage: {util.gpu}%"
        except Exception:
            gpu_text = "GPU Usage: Not available"
        self.gpu_label.config(text=gpu_text)

        self.after(1000, self.update_stats)

    def unzip_trex(self):
        zip_name = "t-rex-0.26.8-win.zip"
        extract_path = os.path.join(os.getcwd(), "Miner")
        trex_path = os.path.join(extract_path, "t-rex.exe")

        if not os.path.exists(trex_path):
            try:
                with zipfile.ZipFile(zip_name, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка распаковки: {e}")
                return None
        return trex_path

    def start_mining(self):
        if self.miner_process and self.miner_process.poll() is None:
            self.status_label.config(text="Miner already running", foreground="orange")
            return

        trex_path = self.unzip_trex()
        if not trex_path or not os.path.exists(trex_path):
            messagebox.showerror("Ошибка", "Файл t-rex.exe не найден после распаковки.")
            self.status_label.config(text="Miner not found", foreground="red")
            return

        algo, pool, wallet = self.detect_mining_params()
        worker = "MyWorker"

        if not algo or not pool or not wallet:
            self.status_label.config(text="GPU не подходит", foreground="red")
            return

        cmd = [
            trex_path,
            "-a", algo,
            "-o", pool,
            "-u", f"{wallet}.{worker}",
            "-p", "x"
        ]

        try:
            self.miner_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.status_label.config(text="Miner started", foreground="green")
        except Exception as e:
            self.status_label.config(text=f"Ошибка запуска: {e}", foreground="red")

    def update_balance(self):
        threading.Thread(target=self.fetch_balance, daemon=True).start()
        self.after(60000, self.update_balance)

    def fetch_balance(self):
        algo, pool, wallet = self.detect_mining_params()
        if wallet == "":
            self.balance_label.config(text="Balance: N/A")
            self.workers_label.config(text="Workers: N/A")
            return

        if algo == "kawpow":
            url = f"https://api.2miners.com/v1/rvn/address/{wallet}"
        elif algo == "ethash":
            self.balance_label.config(text="Balance: N/A (ETH API not implemented)")
            self.workers_label.config(text="Workers: N/A")
            return
        else:
            self.balance_label.config(text="Balance: N/A")
            self.workers_label.config(text="Workers: N/A")
            return

        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            balance = data.get("balance", None)
            workers = len(data.get("workers", []))
            if balance is not None:
                self.balance_label.config(text=f"Balance: {balance} RVN")
            else:
                self.balance_label.config(text="Balance: error")
            self.workers_label.config(text=f"Workers: {workers}")
        except Exception:
            self.balance_label.config(text="Balance: error")
            self.workers_label.config(text="Workers: error")

    def stop_mining(self):
        if self.miner_process and self.miner_process.poll() is None:
            self.miner_process.terminate()
            self.status_label.config(text="Miner stopped", foreground="red")
        else:
            self.status_label.config(text="Miner not running", foreground="orange")

    def hide_window(self):
        self.withdraw()
        self.icon.visible = True

    def show_window(self, icon, item):
        self.icon.visible = False
        self.deiconify()

    def create_tray_icon(self):
        image = Image.new('RGB', (64, 64), color='black')
        self.icon = pystray.Icon("miner_app", image, "Miner App", menu=pystray.Menu(
            pystray.MenuItem("Показать", self.show_window),
            pystray.MenuItem("Выход", self.exit_app)
        ))
        threading.Thread(target=self.icon.run, daemon=True).start()

    def exit_app(self):
        if self.miner_process and self.miner_process.poll() is None:
            self.miner_process.terminate()
        self.icon.stop()
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = MinerApp()
    app.mainloop()
