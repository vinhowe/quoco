#!/usr/bin/env python3.7
import base64
import datetime
import json
import subprocess
import tempfile
import uuid
from getpass import getpass
from os import path, mkdir, urandom
from typing import List, Tuple
import atexit

from cryptography.exceptions import InvalidSignature
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

temp_edit_files: List[Tuple[tempfile.NamedTemporaryFile, str]] = []


# noinspection PyBroadException
def remove_temp_files() -> None:
    global temp_edit_files

    for file_obj, path_str in temp_edit_files:
        try:
            subprocess.run(f"shred -u {path_str}", shell=True)
        except:
            pass

        try:
            file_obj.close()
        except:
            pass

    temp_edit_files = []


def jour_one() -> datetime.date:
    return datetime.date(2020, 1, 17)


def today_date_string() -> str:
    now = datetime.datetime.now()

    return now.strftime("%-m.%-d.%Y")


def entry_filename(date) -> str:
    return f"{date}.lj"


def read_file(filename, key) -> str:
    fernet = Fernet(key)
    with open(filename, "rb") as encrypted_file:
        return fernet.decrypt(encrypted_file.read())


def edit_file(filename: str, key: str) -> None:
    temp_edit_file = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".md")

    temp_edit_files.append((temp_edit_file, temp_edit_file.name))

    decrypted_content = read_file(filename, key)

    temp_edit_file.write(decrypted_content)
    temp_edit_file.flush()

    command = f'vi + "+set noswapfile" {temp_edit_file.name}'

    subprocess.call(command, shell=True)

    with open(temp_edit_file.name) as read_temp_edit_file:
        write_file(read_temp_edit_file.read(), filename, key)

    # Should only be one file that's being closed
    remove_temp_files()


def file_exists(filename):
    return path.exists(filename)


def write_file(content, filename, key):
    fernet = Fernet(key)
    today_file = open(filename, "w+b")

    content_encrypted = fernet.encrypt(content.encode())
    today_file.write(content_encrypted)

    today_file.close()


def entry_in_catalog(entry_name: str, catalog: List[dict]):
    for entry in catalog:
        if entry["name"] == entry_name:
            return entry
    return None


def open_journal_entry(date, key, catalog, catalog_name) -> None:
    entry = entry_in_catalog(date, catalog["entries"])

    if entry is None or not file_exists(entry_filename(entry["obfuscatedName"])):
        days_since_jour_one = (jour_one() - datetime.datetime.now().date()).days
        header = f"# {date} \nday {days_since_jour_one}\n\n\n"
        if entry is None:
            obfuscated_name = uuid.uuid4().hex
            entry = {"name": date, "obfuscatedName": obfuscated_name}
            catalog["entries"].append(entry)
            write_file(json.dumps(catalog), catalog_name, key)
        else:
            obfuscated_name = entry["obfuscatedName"]
        write_file(header, entry_filename(obfuscated_name), key)

    edit_file(f"{entry['obfuscatedName']}.lj", key)


def gen_password_key(password: str, b64_salt: bytes):
    """
    https://nitratine.net/blog/post/encryption-and-decryption-in-python/
    :param b64_salt:
    :param password:
    :return:
    """
    password_encoded = password.encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=base64.b64decode(b64_salt),
        iterations=100000,
        backend=default_backend(),
    )
    return base64.urlsafe_b64encode(kdf.derive(password_encoded))


def check_catalog(catalog_name, salt):
    if not file_exists(catalog_name):
        print("no catalog file found")
        while True:
            password = getpass("enter a new password: ")
            password_confirm = getpass("confirm password: ")

            if password == password_confirm:
                break

            print("passwords don't match. try again.\n")

        # Space between this and the next password prompt
        print()
        key = gen_password_key(password, salt)
        write_file(json.dumps({"entries": []}), catalog_name, key)


def get_lj_path(filename: str) -> str:
    lj_dir_path = ".lj/"

    if not file_exists(lj_dir_path):
        mkdir(lj_dir_path)

    return path.abspath(path.join(lj_dir_path, filename))


def load_secrets():
    secrets_file_name = "secrets.json"
    if not file_exists(get_lj_path(secrets_file_name)):
        secrets = {"salt": str(base64.b64encode(urandom(16)))}
        with open(get_lj_path(secrets_file_name), "w") as secrets_file:
            json.dump(secrets, secrets_file)
        return secrets

    with open(get_lj_path(secrets_file_name), "r") as secrets_file:
        return json.load(secrets_file)


def launch_journal_editor(date_string=None) -> None:
    secrets = load_secrets()

    salt = secrets["salt"]

    catalog_name = get_lj_path(".ljcatalog")
    # If no catalog exists, we will need to make one
    check_catalog(catalog_name, salt)
    catalog = None

    while True:
        password = getpass("enter your password: ")
        key = gen_password_key(password, salt)
        try:
            catalog = json.loads(read_file(catalog_name, key))
        except InvalidToken:
            print("invalid password")
            continue
        break
        # TODO make sure this exits on when the right password is entered

    date = date_string if date_string is not None else today_date_string()

    # Need to remove temp files before closing
    atexit.register(remove_temp_files)

    open_journal_entry(date, key, catalog, catalog_name)

    post_run_date = today_date_string()

    # date_changed = not file_exists(date_filename(post_run_date))

    # if date_changed:
    #     launch_journal_editor(post_run_date)


launch_journal_editor()
