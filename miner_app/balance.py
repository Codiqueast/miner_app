# запрос баланса и воркеров

import requests

def fetch_balance(algo, wallet):
    if algo == "kawpow":
        url = f"https://api.2miners.com/v1/rvn/address/{wallet}"
    else:
        return None, None
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get("balance", "error"), len(data.get("workers", []))
    except:
        return "error", "error"
