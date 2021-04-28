import json
import subprocess
import sys
from base64 import b64decode
from getpass import getpass
from pathlib import Path
from typing import List, Union
from xdg import xdg_data_home, xdg_config_home

import quocofs

from .util.secure_term import add_lines, secure_print, clear_term
from .util.fs import local_file_exists

DEFAULT_EDITOR_CONFIG = {"orientation": "horizontal"}
DOCUMENT_CONFIG_FILENAME = "document_config.json"


class QuocoFsManager:
    # TODO: Salt should ideally be generated and managed by quocofs
    DEFAULT_SALT = "LCzJKR9jSyc42WHBrTaUMg=="

    session: quocofs.Session

    def __init__(
        self, data_path: Union[str, Path], config_path: Union[str, Path], salt: bytes
    ):
        self._data_path = data_path if data_path is Path else Path(data_path)
        self._config_path = config_path if config_path is Path else Path(config_path)
        self._salt = salt
        self.initialize_session_interactive()

    def create_data_path(self):
        Path(self._data_path).mkdir(parents=True, exist_ok=True)

    def create_config_path(self):
        Path(self._config_path).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def default_data_path():
        # TODO(vinhowe): Make this work on Windows too
        # (though I think there are a few more major changes we'd need to make before quoco works on Windows)
        return Path(xdg_data_home(), "quoco")

    # TODO: Move the default config path out of this class because we'll store things like plan templates there
    @staticmethod
    def default_config_path():
        # TODO(vinhowe): Make this work on Windows too
        return Path(xdg_config_home(), "quoco")

    def is_initialized(self):
        return self.session is not None

    def generate_key(self, password: str) -> bytes:
        # TODO: Storing the hash this way is insecure and should be done a better way
        #  (like storing generating the salt and storing it in plaintext in the fs)
        salt = b64decode(self._salt)
        return quocofs.key(password, salt)

    @staticmethod
    def prompt_password(repeat=False):
        def clearable_password_prompt(text):
            add_lines()
            try:
                password = getpass(text)
            except KeyboardInterrupt:
                sys.exit(0)
            return password

        while True:
            password = clearable_password_prompt("enter your password: ")
            if not repeat or password == clearable_password_prompt(
                "repeat your password: "
            ):
                return password
            secure_print("passwords don't match, try again")
            secure_print()

    def _create_remote_accessor(self):
        # TODO: Extend this once we add more remote accessors (S3, Azure, etc.)
        google_service_account_path = Path(
            self._config_path, "google-service-account.json"
        )
        # TODO: Raise custom exception when we can't find a key file.
        #  We can have an offline mode once we actually handle conflicts instead of just overwriting from remote at the
        #  beginning of every session.
        return quocofs.GoogleStorageAccessorConfig(
            "quocofs", str(google_service_account_path)
        )

    def initialize_session(self, password: str):
        self.create_data_path()
        self.create_config_path()

        self.session = quocofs.Session(
            str(self._data_path),
            self.generate_key(password),
            self._create_remote_accessor(),
        )

    def initialize_session_interactive(self):
        add_lines()
        clear_term()
        while True:
            password = self.prompt_password()
            try:
                # TODO: This flow gives the user absolutely no indication whether it found remote data
                self.initialize_session(password)
            except quocofs.DecryptionError:
                secure_print("password failed to decrypt, please try again")
                secure_print()
                continue
            break

    def edit_documents_vim(self, ids: List[bytes]) -> None:
        documents_read_info = []
        document_config = DEFAULT_EDITOR_CONFIG

        if local_file_exists(DOCUMENT_CONFIG_FILENAME):
            with open(DOCUMENT_CONFIG_FILENAME) as document_config_data:
                # Make sure to include any default keys
                document_config = {**document_config, **json.load(document_config_data)}

        for id in ids:
            path = self.session.object_temp_file(id, "md")
            documents_read_info.append(
                {
                    "path": path,
                    "id": id,
                }
            )

        # https://vi.stackexchange.com/questions/6177/the-simplest-way-to-start-vim-in-private-mode
        # `set noswapfile` prevents vim from making a swap file for the session
        # `set viminfo=` prevents vim from outputting operations and commands in
        # plaintext to ~/.viminfo
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

        temp_paths = [v["path"] for v in documents_read_info]
        files_argument = " ".join(temp_paths)
        if len(documents_read_info) > 1:
            split_switch = "o" if document_config["orientation"] == "vertical" else "O"
            files_argument = f"-{split_switch} {files_argument}"
            # Account for Vim's "2 files to edit" output
            add_lines()

        vim_path = (
            document_config["vim_path"] if "vim_path" in document_config else "vim"
        )

        command = f'{vim_path} + "+{vi_secure_settings_string}" {files_argument}'

        subprocess.call(command, shell=True)

    def edit_document_vim(self, name: bytes) -> None:
        self.edit_documents_vim([name])

    def __enter__(self):
        self.session.__enter__()

    def __exit__(self, *args):
        self.session.__exit__(*args)
