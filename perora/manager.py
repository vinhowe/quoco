import json
from time import sleep
from tempfile import NamedTemporaryFile, TemporaryDirectory

from .document import open_service_interactive
from .secure_fs_io import _secure_delete_file


def edit_catalog(service_name: str) -> None:
    with NamedTemporaryFile(suffix=".json", mode="w") as temp_catalog_file:
        key, catalog = open_service_interactive(service_name)
        data = json.dumps(catalog.serialize(), indent=4)
        temp_catalog_file.write(data)
        print(data)
        print(temp_catalog_file.name)
        try:
            while True:
                sleep(1)
        except KeyboardInterrupt:
            print("interrupted, deleting file")
        _secure_delete_file(temp_catalog_file.name)


# TODO: Just for debugging, get rid of this
if __name__ == "__main__":
    edit_catalog("plan")