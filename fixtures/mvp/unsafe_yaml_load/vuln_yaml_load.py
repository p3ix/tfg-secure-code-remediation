import yaml

def load_config(data: str):
    return yaml.load(data, Loader=yaml.Loader)
