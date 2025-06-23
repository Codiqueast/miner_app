# CPU, RAM, общая нагрузка (через psutil)

import psutil

def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def get_ram_usage():
    return psutil.virtual_memory().percent
