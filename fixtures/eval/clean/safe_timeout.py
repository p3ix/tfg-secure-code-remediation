"""Variante segura de petición HTTP: `timeout` explícito.

No debe disparar la categoría `missing_timeout` (B113).
"""

import requests


def fetch():
    return requests.get("https://api.example.com/data", timeout=5)
