import json
import os
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from getpass import getpass
from shutil import which
from typing import Dict, Union, List

from cryptography.fernet import InvalidToken

from perora.fs_util import _data_path, _per_ext_file, file_exists, mkdir_if_not_exist
from perora.secure_fs_io import (
    _read_decrypt_file,
    _write_encrypt_file,
    _gen_password_key,
    default_salt,
    _secure_delete_file)
from perora.secure_term import clear_term, add_lines, secure_print

catalog_file_name = "catalog"
documents_dir_name = "documents"


@dataclass
class DocumentInfo:
    name: str
    obfuscated_name: str

    def serialize(self) -> dict:
        return {"name": self.name, "obfuscatedName": self.obfuscated_name}

    # TODO: see if there isn't a more elegant way to get this service_name in here
    def real_path(self, service_name: str):
        return _documents_path(service_name, _per_ext_file(self.obfuscated_name))

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
                _documents_path(service_name, _per_ext_file(catalog_file_name)), key
            )
        )
    )
    # Add to cache
    _catalogs[catalog.service_name] = catalog
    return catalog


def _flush_catalog(
        catalog: Union[Catalog, dict], service_name: str, key: str
) -> _write_encrypt_file:
    path = _documents_path(service_name, _per_ext_file(catalog_file_name))
    catalog_data = catalog.serialize() if catalog is Catalog else catalog

    # Should return whatever _write_encrypt_file does (right now, None)
    return _write_encrypt_file(json.dumps(catalog_data.serialize()), path, key)


def _catalog(service_name: str, key: str) -> Catalog:
    if service_name in _catalogs:
        return _catalogs[service_name]

    return _load_catalog_from_file(service_name, key)


def _documents_path(service_name: str, *paths):
    path = _data_path(service_name, documents_dir_name)
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
    return _documents_path(service_name, _per_ext_file(obfuscated_name))


def _document_filename_or_create(service_name: str, document_name: str, key: str):
    catalog = _catalog(service_name, key)

    existing_filename = _document_filename(service_name, document_name, key)
    if existing_filename is not None:
        return existing_filename

    obfuscated_name = uuid.uuid4().hex

    catalog.documents[document_name] = DocumentInfo(document_name, obfuscated_name)
    _flush_catalog(catalog, service_name, key)

    return _documents_path(service_name, _per_ext_file(obfuscated_name))


def read_document(service_name: str, document_name: str, key: str):
    document_filename = _document_filename(service_name, document_name, key)
    return None if document_filename is None else _read_decrypt_file(document_filename, key)


def write_document(content: str, service_name: str, document_name: str, key: str):
    document_filename = _document_filename_or_create(service_name, document_name, key)
    return _write_encrypt_file(content, document_filename, key)


def rename_document(service_name: str, document_name: str, new_document_name: str, key: str):
    catalog = _catalog(service_name, key)
    if document_name not in catalog.documents:
        return

    document = catalog.documents[document_name]
    updated_document = DocumentInfo(new_document_name, document.obfuscated_name)

    catalog.documents[new_document_name] = updated_document
    _flush_catalog(catalog, service_name, key)


def delete_document(service_name: str, document_name: str, key: str) -> None:
    catalog = _catalog(service_name, key)
    document_filename = _document_filename(service_name, document_name, key)
    if document_filename is None:
        return
    del catalog.documents[document_name]
    _flush_catalog(catalog, service_name, key)
    return _secure_delete_file(document_filename)


def catalog_exists_or_create(service_name: str, salt: str) -> None:
    """
    Check if catalog file exists with name exists or create it
    :param service_name:
    :param salt:
    """
    if not file_exists(_documents_path(service_name, _per_ext_file(catalog_file_name))):
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


def password_prompt(service_name: str, salt: str = default_salt):
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
    return key, catalog


def _remove_temp_file(file_obj: tempfile.NamedTemporaryFile, path_str: str) -> None:
    _secure_delete_file(path_str)

    try:
        file_obj.close()
    except:
        # TODO: Find what error (if any, if not, get rid of this) is thrown when a file object has already been closed
        pass


def edit_documents(service_name: str, names: List[str], key: str) -> None:
    documents_read_info = []

    for name in names:
        temp_edit_file = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".md")
        decrypted_content = read_document(service_name, name, key)

        temp_edit_file.write(decrypted_content)
        temp_edit_file.flush()
        documents_read_info.append({
            "temp_file": temp_edit_file,
            "temp_file_path": temp_edit_file.name,
            "name": name,
            "content": decrypted_content
        })

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

    # https://vi.stackexchange.com/questions/6177/the-simplest-way-to-start-vim-in-private-mode
    # `set noswapfile` prevents vim from making a swap file for the session
    # `set viminfo=` prevents vim from outputting operations and commands in plaintext to ~/.viminfo

    files_argument = " ".join([v["temp_file_path"] for v in documents_read_info])
    if len(documents_read_info) > 1:
        files_argument = f"-O {files_argument}"
        # Account for Vim's "2 files to edit" output
        add_lines()
    else:
        # TODO: Find out why this is needed
        add_lines(-1)

    command = f'vi + "+{vi_secure_settings_string}" {files_argument}'

    subprocess.call(command, shell=True)

    for info in documents_read_info:
        with open(info["temp_file_path"]) as read_temp_edit_file:
            write_document(read_temp_edit_file.read(), service_name, info["name"], key)

        # Should only be on file that's being closed
        _remove_temp_file(info["temp_file"], info["temp_file_path"])

    clear_term()


def edit_document(service_name: str, name: str, key: str) -> None:
    edit_documents(service_name, [name], key)
