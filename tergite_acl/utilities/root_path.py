from pathlib import Path

def get_project_root() -> Path:
    return Path(__file__).parent.parent

def get_data_directory() -> Path:
    return get_project_root() / 'data_directory'


data_directory = get_data_directory()

project_root = get_project_root()
