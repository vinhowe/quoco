import os
from pathlib import Path

data_dir = "data"
per_ext = "per"


def file_exists(filename) -> bool:
    return os.path.exists(filename)


def mkdir_if_not_exist(dir_path: str) -> None:
    if not file_exists(dir_path):
        os.mkdir(dir_path)


def per_ext_file(filename: str) -> str:
    return f"{filename}.{per_ext}"


def touch_file(filename: str) -> bool:
    if file_exists(filename):
        return False

    Path(filename).touch()


def data_path(service_name: str, *paths: str) -> str:
    mkdir_if_not_exist(data_dir)

    abs_data_subdir = os.path.join(data_dir, service_name)

    mkdir_if_not_exist(abs_data_subdir)

    return os.path.join(abs_data_subdir, *paths)
