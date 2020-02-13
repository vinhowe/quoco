import base64
import os
import subprocess
import tempfile
from shutil import which

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from perora.fs_util import file_exists

# TODO: Generate a new salt for every fresh installation instead
default_salt = "LCzJKR9jSyc42WHBrTaUMg=="


def _read_decrypt_file(filename: str, key: str) -> bytes:
    fernet = Fernet(key)
    # THIS SHOULD SAY "rb" in production
    with open(filename, "rb") as encrypted_file:
        # TODO: REMOVE--FOR DEBUGGING PURPOSES ONLY
        return fernet.decrypt(encrypted_file.read())
        # return bytes(encrypted_file.read(), encoding="utf8")


def _write_encrypt_file(content: str, filename: str, key: str) -> None:
    fernet = Fernet(key)
    encrypt_file = open(filename, "w+b")

    content_encrypted = fernet.encrypt(content.encode())
    # TODO: REMOVE--FOR DEBUGGING PURPOSES ONLY
    encrypt_file.write(content_encrypted)
    # encrypt_file.write(bytes(content, encoding="utf8"))

    encrypt_file.close()


def _secure_delete_file(path_str) -> None:
    if not file_exists(path_str):
        return

    if which("shred") is not None:
        subprocess.run(f"shred -u {path_str}", shell=True)
    elif which("srm") is not None:
        subprocess.run(f"srm {path_str}", shell=True)
    else:
        os.remove(path_str)


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
    if not file_exists(path_str):
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
