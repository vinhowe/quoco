import json
import os
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from getpass import getpass
from typing import Dict, Union, List
import atexit

from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler,
    FileSystemEvent,
)
from cryptography.fernet import InvalidToken

from perora.fs_util import (
    data_path,
    per_ext_file,
    mkdir_if_not_exist,
    local_file_exists,
)
from perora.secure_fs_io import (
    _read_decrypt_file,
    _write_encrypt_file,
    _gen_password_key,
    default_salt,
    _secure_delete_file,
    remote_file_exists,
    remote_file_touch,
    remote_file_delete,
)
from perora.secure_term import clear_term, add_lines, secure_print

catalog_file_name = "catalog"
documents_dir_name = "documents"
lock_filename = ".plock"

document_config_filename = "document_config.json"
default_document_config = {"orientation": "horizontal"}

open_services = []


@dataclass
class DocumentInfo:
    name: str
    obfuscated_name: str

    def serialize(self) -> dict:
        return {"name": self.name, "obfuscatedName": self.obfuscated_name}

    # TODO: see if there isn't a more elegant way to get this service_name in here
    def real_path(self, service_name: str):
        return _documents_path(service_name, per_ext_file(self.obfuscated_name))

    @staticmethod
    def deserialize(data: dict):
        return DocumentInfo(data["name"], data["obfuscatedName"])


@dataclass
class Catalog:
    service_name: str
    documents: Dict[str, DocumentInfo]

    def serialize(self) -> dict:
        return {
            "serviceName": self.service_name,
            "documents": {
                document_name: document.serialize()
                for document_name, document in self.documents.items()
            },
        }

    @staticmethod
    def deserialize(data: dict):
        service_name = data["serviceName"]
        documents = {
            document_name: DocumentInfo.deserialize(document)
            for document_name, document in data["documents"].items()
        }
        return Catalog(service_name, documents)


_catalogs: Dict[str, Catalog] = {}


def _load_catalog_from_file(service_name: str, key: str) -> Catalog:
    # Rethrows `cryptography` lib `InvalidToken` errors
    catalog = Catalog.deserialize(
        json.loads(
            _read_decrypt_file(
                _documents_path(service_name, per_ext_file(catalog_file_name)), key
            )
        )
    )
    # Add to cache
    _catalogs[catalog.service_name] = catalog
    return catalog


def _flush_catalog(
    catalog: Union[Catalog, dict], service_name: str, key: str
) -> _write_encrypt_file:
    path = _documents_path(service_name, per_ext_file(catalog_file_name))
    catalog_data = catalog.serialize() if catalog is Catalog else catalog

    # Should return whatever _write_encrypt_file does (right now, None)
    return _write_encrypt_file(json.dumps(catalog_data.serialize()), path, key)


def _catalog(service_name: str, key: str) -> Catalog:
    if service_name in _catalogs:
        return _catalogs[service_name]

    return _load_catalog_from_file(service_name, key)


def _documents_path(service_name: str, *paths):
    path = data_path(service_name, documents_dir_name)
    mkdir_if_not_exist(path)

    return os.path.join(path, *paths)


def document_in_catalog(service_name: str, document_name: str, key):
    catalog = _catalog(service_name, key)
    return document_name in catalog.documents


def _document_filename(service_name: str, document_name: str, key):
    catalog = _catalog(service_name, key)

    if not document_in_catalog(service_name, document_name, key):
        return None

    obfuscated_name = catalog.documents[document_name].obfuscated_name
    return _documents_path(service_name, per_ext_file(obfuscated_name))


def _document_filename_or_create(service_name: str, document_name: str, key: str):
    catalog = _catalog(service_name, key)

    existing_filename = _document_filename(service_name, document_name, key)
    if existing_filename is not None:
        return existing_filename

    obfuscated_name = uuid.uuid4().hex

    catalog.documents[document_name] = DocumentInfo(document_name, obfuscated_name)
    _flush_catalog(catalog, service_name, key)

    return _documents_path(service_name, per_ext_file(obfuscated_name))


def read_document(service_name: str, document_name: str, key: str):
    document_filename = _document_filename(service_name, document_name, key)
    return (
        None
        if document_filename is None
        else _read_decrypt_file(document_filename, key)
    )


def write_document(content: str, service_name: str, document_name: str, key: str):
    document_filename = _document_filename_or_create(service_name, document_name, key)
    return _write_encrypt_file(content, document_filename, key)


def rename_document(
    service_name: str, document_name: str, new_document_name: str, key: str
):
    catalog = _catalog(service_name, key)
    if document_name not in catalog.documents:
        return

    document = catalog.documents[document_name]
    updated_document = DocumentInfo(new_document_name, document.obfuscated_name)

    catalog.documents[new_document_name] = updated_document
    _flush_catalog(catalog, service_name, key)


def delete_document(service_name: str, document_name: str, key: str) -> bool:
    catalog = _catalog(service_name, key)
    document_filename = _document_filename(service_name, document_name, key)
    if document_filename is None:
        return False
    del catalog.documents[document_name]
    _flush_catalog(catalog, service_name, key)
    return remote_file_delete(document_filename)


def catalog_exists_or_create(service_name: str, salt: str) -> None:
    """
    Check if catalog file exists with name exists or create it
    :param service_name:
    :param salt:
    """
    if not remote_file_exists(
        _documents_path(service_name, per_ext_file(catalog_file_name))
    ):
        secure_print(f"no catalog file found for {service_name} service")
        while True:
            password = getpass("enter a new password: ")
            password_confirm = getpass("confirm password: ")

            if password == password_confirm:
                break

            secure_print("passwords don't match. try again.\n")

        # Space between this and the next password prompt
        secure_print()
        key = _gen_password_key(password, salt)
        _flush_catalog(Catalog(service_name, {}), service_name, key)


def lock_path(service_name: str) -> str:
    return data_path(service_name, lock_filename)


def quit_if_lock_exists(service_name: str) -> None:
    if remote_file_exists(lock_path(service_name)):
        secure_print(f"another instance of {service_name} service is running")
        exit(1)


def create_lock(service_name: str) -> None:
    remote_file_touch(lock_path(service_name))


def release_lock(service_name: str) -> None:
    remote_file_delete(lock_path(service_name))


def open_service_interactive(service_name: str, salt: str = default_salt):
    if service_name in open_services:
        secure_print(f"{service_name} already open")
        return None
    quit_if_lock_exists(service_name)
    catalog_exists_or_create(service_name, salt)
    while True:
        password = getpass("enter your password: ")
        add_lines()
        clear_term()
        key = _gen_password_key(password, salt)
        try:
            # Test decrypting file
            catalog = _load_catalog_from_file(service_name, key)
        except InvalidToken:
            secure_print("invalid password")
            continue
        break
        # TODO make sure this exits on when the right password is entered
    create_lock(service_name)
    open_services.append(service_name)
    return key, catalog


def _remove_temp_file(file_obj: tempfile.NamedTemporaryFile, path_str: str) -> None:
    _secure_delete_file(path_str)

    try:
        file_obj.close()
    except:
        # TODO: Find what error (if any, if not, get rid of this) is thrown when a
        #  file object has already been closed
        pass


class DocumentEditorManager:
    # Set the directory on watch
    def __init__(
        self, service_name: str, root_path: str, paths_map: Dict[str, str], command, key
    ):
        self._key = key
        self._service_name = service_name
        self._root_path = root_path
        self._paths_map = paths_map
        self._command = command
        self._observer = Observer()

    def run(self) -> None:
        event_handler = DocumentFilesEventHandler(
            self._service_name, self._paths_map, self._key
        )
        self._observer.schedule(event_handler, self._root_path)
        self._observer.start()
        try:
            subprocess.call(self._command, shell=True)
        except Exception as e:
            print(e)
        finally:
            self._observer.stop()

        self._observer.join()


class DocumentFilesEventHandler(FileSystemEventHandler):
    def __init__(self, service_name, paths_map, key) -> None:
        self._key = key
        self._service_name = service_name
        self._paths_map = paths_map

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return None

        if event.event_type == "modified" and event.src_path in self._paths_map:
            with open(event.src_path) as read_temp_edit_file:
                write_document(
                    read_temp_edit_file.read(),
                    self._service_name,
                    self._paths_map[event.src_path],
                    self._key,
                )


def edit_documents(service_name: str, names: List[str], key: str) -> None:
    documents_read_info = []
    document_config = default_document_config

    if local_file_exists(document_config_filename):
        with open(document_config_filename) as document_config_data:
            # Make sure to include any default keys
            document_config = {
                **document_config,
                **json.load(document_config_data),
            }

    with tempfile.TemporaryDirectory() as temp_dir:
        for name in names:
            temp_edit_file = tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".md", dir=temp_dir
            )
            decrypted_content = read_document(service_name, name, key)

            temp_edit_file.write(decrypted_content)
            temp_edit_file.flush()
            documents_read_info.append(
                {
                    "temp_file": temp_edit_file,
                    "temp_file_path": temp_edit_file.name,
                    "name": name,
                    "content": decrypted_content,
                }
            )

        vi_secure_settings = [
            "history=0",
            "nobackup",
            "nomodeline",
            "noshelltemp",
            "noswapfile",
            "noundofile",
            "nowritebackup",
            "secure",
            "viminfo=",
        ]

        vi_secure_settings_string = " | ".join(
            list(map(lambda s: f"set {s}", vi_secure_settings))
        )

        # https://vi.stackexchange.com/questions/6177/the-simplest-way-to-start-vim-in
        # -private-mode
        # `set noswapfile` prevents vim from making a swap file for the session
        # `set viminfo=` prevents vim from outputting operations and commands in
        # plaintext to ~/.viminfo
        temp_paths = [v["temp_file_path"] for v in documents_read_info]
        files_argument = " ".join(temp_paths)
        if len(documents_read_info) > 1:
            split_switch = "o" if document_config["orientation"] == "vertical" else "O"
            files_argument = f"-{split_switch} {files_argument}"
            # Account for Vim's "2 files to edit" output
            add_lines()

        command = f'vi + "+{vi_secure_settings_string}" {files_argument}'

        # subprocess.call(command, shell=True)
        paths_map = {v["temp_file_path"]: v["name"] for v in documents_read_info}
        print(paths_map)
        DocumentEditorManager(service_name, temp_dir, paths_map, command, key).run()

        document_names = ", ".join([f"'{name}'" for name in names])
        secure_print(f"uploading document(s): {document_names}")

        # Final pass in case listeners missed anything

        for info in documents_read_info:
            with open(info["temp_file_path"]) as read_temp_edit_file:
                write_document(
                    read_temp_edit_file.read(), service_name, info["name"], key
                )

            # Should only be on file that's being closed
            _remove_temp_file(info["temp_file"], info["temp_file_path"])

        # clear_term()


def edit_document(service_name: str, name: str, key: str) -> None:
    edit_documents(service_name, [name], key)


def close_services():
    for service_name in open_services:
        release_lock(service_name)


atexit.register(close_services)
