import json

def load_config(file_path):
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        raise
    except Exception as e:
        raise 

