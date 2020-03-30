import base64
import os
import subprocess
import tempfile
from io import BytesIO
from shutil import which

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from google.auth.exceptions import TransportError
from google.cloud import storage
from google.cloud.exceptions import NotFound
from google.cloud.storage import Blob
from requests import ReadTimeout
from urllib3.exceptions import ProtocolError

from perora.fs_util import local_file_exists
from perora.secure_term import secure_input

# TODO: Generate a new salt for every fresh installation instead
default_salt = "LCzJKR9jSyc42WHBrTaUMg=="

service_account_json_path = "service-account.json"
bucket_name = "perora-data"

storage_client = storage.client.Client.from_service_account_json(
    service_account_json_path
)

bucket = storage_client.bucket(bucket_name)

max_retries = 1


def remote_file_exists(filename: str) -> bool:
    blob = bucket.blob(filename)
    exists = None
    while exists is None:
        try:
            exists = blob.exists(timeout=10)
        except (TransportError, ReadTimeout, ConnectionError, ProtocolError):
            pass
        if exists is None:
            secure_input("failed to check if file exists--press enter to retry")
    return exists


def _upload_file(content: bytes, filename: str) -> bool:
    blob = bucket.blob(filename)
    try:
        string_buffer = BytesIO(content)
        blob.upload_from_file(
            file_obj=string_buffer,
            size=len(content),
            content_type="text/plain",
            num_retries=max_retries,
        )
        return True
    except (ReadTimeout, TransportError, ConnectionError, ProtocolError):
        # NO SECURE PRINT HERE
        return False


def _download_file(filename: str):
    blob = bucket.blob(filename)
    try:
        return blob.download_as_string()
    except (ReadTimeout, TransportError, ConnectionError, ProtocolError):
        return False


def _read_decrypt_file(filename: str, key: str) -> bytes:
    fernet = Fernet(key)
    encrypted_file = None
    while not encrypted_file:
        encrypted_file = _download_file(filename)
        if not encrypted_file:
            secure_input("failed to download file--press enter to retry")
    return fernet.decrypt(encrypted_file).decode("utf-8")


def _write_encrypt_file(content: str, filename: str, key: str) -> None:
    fernet = Fernet(key)
    content_encrypted = fernet.encrypt(content.encode())
    result = None
    while not result:
        result = _upload_file(content_encrypted, filename)
        if not result:
            secure_input("failed to upload file--press enter to retry")


def _secure_delete_file(path_str) -> None:
    if not local_file_exists(path_str):
        return

    if which("shred") is not None:
        subprocess.run(f"shred -u {path_str}", shell=True)
    elif which("srm") is not None:
        subprocess.run(f"srm {path_str}", shell=True)
    else:
        os.remove(path_str)


def remote_file_delete(filename: str) -> bool:
    blob: Blob = bucket.blob(filename)
    while True:
        try:
            blob.delete(timeout=10)
            return True
        except NotFound:
            return False
        except (TransportError, ReadTimeout, ConnectionError, ProtocolError):
            secure_input("failed to delete file--press enter to retry")
            continue


def remote_file_touch(filename: str) -> bool:
    result = None
    while not result:
        result = _upload_file(b"", filename)
        if not result:
            secure_input("failed to touch file--press enter to retry")


def _gen_password_key(password: str, b64_salt: str = "LCzJKR9jSyc42WHBrTaUMg=="):
    # TODO: Automatically generate salt in file for user if doesn't exist;
    #  shouldn't have a salt in code
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


def _secure_delete_file(path_str) -> None:
    if not remote_file_exists(path_str):
        return

    if which("shred") is not None:
        subprocess.run(f"shred -u {path_str}", shell=True)
    elif which("srm") is not None:
        subprocess.run(f"srm {path_str}", shell=True)
    else:
        os.remove(path_str)


def _remove_temp_file(file_obj: tempfile.NamedTemporaryFile, path_str: str) -> None:
    _secure_delete_file(path_str)

    try:
        file_obj.close()
    except:
        # TODO: Find what error (if any, if not, get rid of this) is thrown when a file object has already been closed
        pass
