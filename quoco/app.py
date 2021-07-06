import json
from base64 import b64decode

import quocofs

from quoco.quocofs_manager import QuocoFsManager
from .plan import whats_the_plan
from .quocofs_migration import migrate_plan
import argparse


def decrypt(filename):
    key = quocofs.key(
        QuocoFsManager.prompt_password(), b64decode(QuocoFsManager.DEFAULT_SALT)
    )
    with open(filename, "rb") as rfile:
        with open(f"{filename}.decrypted", "wb") as wfile:
            wfile.write(quocofs.loads(rfile.read(), key))


def encrypt(filename):
    key = quocofs.key(
        QuocoFsManager.prompt_password(), b64decode(QuocoFsManager.DEFAULT_SALT)
    )
    with open(filename, "rb") as rfile:
        with open(filename.replace(".decrypted", ""), "wb") as wfile:
            wfile.write(quocofs.dumps(rfile.read(), key))


def decrypt_hashes(filename):
    key = quocofs.key(
        QuocoFsManager.prompt_password(), b64decode(QuocoFsManager.DEFAULT_SALT)
    )
    with open(filename, "rb") as rfile:
        with open(f"{filename}.decrypted", "w") as wfile:
            json.dump(
                {
                    bytes.hex(k): bytes.hex(v)
                    for k, v in quocofs.hashes.loads(rfile.read(), key).items()
                },
                wfile,
            )


def main():
    parser = argparse.ArgumentParser(description="Quoco CLI")
    parser.add_argument("--decrypt")
    parser.add_argument("--encrypt")
    parser.add_argument("--decrypt-hashes")
    parser.add_argument("--migrate")
    args, unknown = parser.parse_known_args()

    if args.decrypt:
        decrypt(args.decrypt)
        return

    if args.encrypt:
        encrypt(args.encrypt)
        return

    if args.decrypt_hashes:
        decrypt_hashes(args.decrypt_hashes)
        return

    if args.migrate:
        migrate_plan(args.migrate)
        return

    whats_the_plan(" ".join(unknown) if len(unknown) else None)


if __name__ == "__main__":
    main()
