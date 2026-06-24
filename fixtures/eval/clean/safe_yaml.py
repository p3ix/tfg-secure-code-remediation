"""Variante segura de carga YAML: `safe_load`.

No debe disparar la categoría `unsafe_yaml_load` (B506).
"""

import yaml


def load(data: str):
    return yaml.safe_load(data)
