import os
import json

def read_config():
    path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    print(path)
    with open(os.path.join(path, "config.json"), "r") as file:
        config = json.load(file)
    
    return config
