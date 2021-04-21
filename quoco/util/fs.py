import os
import subprocess
from pathlib import Path
from shutil import which

data_dir = "data"
per_ext = "per"


def local_file_exists(filename) -> bool:
    return os.path.exists(filename)


def mkdir_if_not_exist(dir_path: str) -> None:
    if not local_file_exists(dir_path):
        os.mkdir(dir_path)


def per_ext_file(filename: str) -> str:
    return f"{filename}.{per_ext}"


def touch_local_file(filename: str) -> bool:
    if local_file_exists(filename):
        return False

    Path(filename).touch()


def data_path(service_name: str, *paths: str) -> str:
    mkdir_if_not_exist(data_dir)

    abs_data_subdir = os.path.join(data_dir, service_name)

    mkdir_if_not_exist(abs_data_subdir)

    return os.path.join(abs_data_subdir, *paths)


def _secure_delete_file(path_str) -> None:
    if not local_file_exists(path_str):
        return

    if which("shred") is not None:
        subprocess.run(f"shred -u {path_str}", shell=True)
    elif which("srm") is not None:
        subprocess.run(f"srm {path_str}", shell=True)
    else:
        os.remove(path_str)
