# интерфейс и окно Tkinter
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image
import keyboard
import pystray

from miner import unzip_trex, start_miner
from gpu_utils import detect_mining_params, detect_gpu_memory
from system_info import get_cpu_usage, get_ram_usage
from balance import fetch_balance
from config import WORKER_NAME


class MinerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Miner Controller")
        self.geometry("400x300")
        self.icon_image = None
        self.miner_process = None

        self.create_widgets()
        self.init_nvml()
        self.launch_miner()
        self.update_stats()
        self.update_balance_loop()
        keyboard.add_hotkey('w', self.stop_mining)
        self.create_tray_icon()

    def init_nvml(self):
        try:
            import py3nvml.py3nvml as nvml
            nvml.nvmlInit()
        except:
            messagebox.showwarning("Внимание", "Не удалось инициализировать NVML. GPU-статистика недоступна.")

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

    def update_stats(self):
        cpu = get_cpu_usage()
        ram = get_ram_usage()
        gpu = detect_gpu_memory()

        self.cpu_label.config(text=f"CPU Usage: {cpu}%")
        self.ram_label.config(text=f"RAM Usage: {ram}%")
        self.gpu_label.config(text=f"GPU VRAM: {gpu:.1f} GB")

        self.after(1000, self.update_stats)

    def launch_miner(self):
        trex_path = unzip_trex()
        if not trex_path:
            self.status_label.config(text="Miner not found", foreground="red")
            return

        algo, pool, wallet = detect_mining_params()
        if not algo:
            self.status_label.config(text="GPU не поддерживается", foreground="red")
            return

        self.miner_process = start_miner(trex_path, algo, pool, wallet, WORKER_NAME)
        self.status_label.config(text="Miner started", foreground="green")

    def update_balance_loop(self):
        threading.Thread(target=self.fetch_and_show_balance, daemon=True).start()
        self.after(60000, self.update_balance_loop)

    def fetch_and_show_balance(self):
        algo, _, wallet = detect_mining_params()
        balance, workers = fetch_balance(algo, wallet)
        self.balance_label.config(text=f"Balance: {balance} RVN")
        self.workers_label.config(text=f"Workers: {workers}")

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
