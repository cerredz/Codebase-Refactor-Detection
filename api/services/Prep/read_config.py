import json
from .paths import get_config_path

def read_config():
    with open(get_config_path(), "r") as file:
        config = json.load(file)
    
    return config
