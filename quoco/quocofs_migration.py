import json
import warnings
from hashlib import sha256
from pathlib import Path
from glob import glob
from typing import Callable, Optional, Type, Union

from .plan import (
    PlanEntryWithDate,
    _load_plan_catalog_interactive,
    PlanEntry,
    PLAN_TYPES,
    PLAN_CATALOG_ENTRIES_KEY,
)


def apply_migration(service_name: str, migration: Callable, path: Union[str, Path]):
    migration_path = Path(path, service_name)

    catalog_path = Path(migration_path, "catalog.json")
    with open(catalog_path) as catalog_file:
        catalog_data = json.load(catalog_file)

    migration(old_catalog=catalog_data, migration_path=migration_path)

    with open(catalog_path, "w") as catalog_file:
        json.dump(catalog_data, catalog_file, indent=4)


def update_field_names(catalog_data, **_):
    if "serviceName" in catalog_data:
        service_name = catalog_data["serviceName"]
        del catalog_data["serviceName"]
        catalog_data["service"] = service_name


def create_hashes(catalog_data: dict, migration_path: str) -> None:
    for document_file_name in glob(str(Path(migration_path, "*.md"))):
        with open(document_file_name, "rb") as document_file:
            print(document_file_name)
            document_hash = sha256(document_file.read()).hexdigest()
            print(document_hash)
            catalog_data["documents"][Path(document_file_name).stem][
                "hash"
            ] = document_hash


def _debug_catalog(catalog_path: str):
    warnings.warn("Deprecated", DeprecationWarning)
    catalog_header = b"perc\0"
    with open(catalog_path, "rb") as catalog_file:
        header_bytes = catalog_file.read(5)
        if header_bytes != catalog_header:
            header_bytes_formatted = bytes.hex(header_bytes, sep=" ", bytes_per_sep=1)
            correct_bytes_formatted = bytes.hex(
                catalog_header, sep=" ", bytes_per_sep=1
            )
            print(
                f"invalid catalog! first 4 bytes: {header_bytes_formatted} (expected {correct_bytes_formatted})"
            )
            return

        print("valid catalog, reading...")

        while True:
            document_name_bytes = catalog_file.read(16)

            if not document_name_bytes:
                # Check if read worked before continuing
                break

            document_name = document_name_bytes.hex()
            # second parameter 1 means seek relative to current position
            catalog_file.seek(1, 1)
            document_hash = catalog_file.read(32).hex()
            print(f"{document_name} {document_hash}")


def migrate_json_to_binary(catalog_data: dict, migration_path: str):
    # Note: I want to get rid of the service distinction and have everything under the same index
    with open(Path(migration_path, "catalog"), "wb") as binary_catalog_file:
        # TODO: Use this code to actually write the file in the future

        file_content = b"perc\0"

        for document in catalog_data["documents"].values():
            hex_name_bytes = bytes.fromhex(document["obfuscatedName"])
            hex_hash_bytes = bytes.fromhex(document["hash"])
            file_content += hex_name_bytes + b"\0" + hex_hash_bytes
        binary_catalog_file.write(file_content)


def plan_from_legacy_name(legacy_name: str) -> Optional[PlanEntry]:
    target_plan_type: Optional[Type[PlanEntry]] = None
    for plan_type in PLAN_TYPES:
        if legacy_name.startswith(plan_type.type_name):
            target_plan_type = plan_type
            break

    if not target_plan_type:
        return None

    if issubclass(target_plan_type, PlanEntryWithDate):
        entry = target_plan_type(target_plan_type.date_from_legacy_name(legacy_name))
    else:
        entry = target_plan_type()

    return entry


def migrate_plan_data_to_new_format(old_catalog: dict, migration_path: str):
    manager, catalog_data, catalog_id = _load_plan_catalog_interactive()

    with manager:
        for document in old_catalog["documents"].values():
            plan_name = document["name"]
            plan_instance = plan_from_legacy_name(plan_name)

            if plan_instance is None:
                continue

            # document_id = document["obfuscatedName"]
            with open(Path(migration_path, f"{plan_name}.md"), "rb") as document_file:
                document_id = bytes.hex(
                    bytes(manager.session.create_object(document_file.read()))
                )

            catalog_data[PLAN_CATALOG_ENTRIES_KEY][
                document_id
            ] = plan_instance.serialize() | {"id": document_id}

        manager.session.modify_object(
            catalog_id, json.dumps(catalog_data).encode("utf-8")
        )


def migrate_plan(path):
    apply_migration("plan", migrate_plan_data_to_new_format, path)
