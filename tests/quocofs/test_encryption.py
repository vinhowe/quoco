import itertools
import random
from typing import Optional

import pytest

import quocofs

_ENCRYPT_RANDOM_BYTES_PARAMETER_CHUNK_COUNT = 3
# This is just a number I picked; higher numbers will be more thorough but will make tests take longer.
_ENCRYPT_RANDOM_BYTES_PARAMETER_CHUNK_PADDING = 64
# 10 digits of tau (2pi).
_ENCRYPT_RANDOM_BYTES_SEED = 6_283185307

_ENCRYPT_RANDOM_BYTES_SIZE = 8192


def _encrypt_random_bytes_params():
    """Generate random test data around chunk boundaries."""
    # TODO(vinhowe): Is there any reason why it would be better to use file data for this?
    random.seed(_ENCRYPT_RANDOM_BYTES_SEED)
    return [
        pytest.param(random.randbytes(n), id=f"{n} bytes")
        for n in itertools.chain.from_iterable(
            range(
                max(
                    0,
                    chunk_boundary - _ENCRYPT_RANDOM_BYTES_PARAMETER_CHUNK_PADDING,
                ),
                chunk_boundary + _ENCRYPT_RANDOM_BYTES_PARAMETER_CHUNK_PADDING,
            )
            for chunk_boundary in [
                chunk_i * quocofs.CHUNK_LENGTH
                for chunk_i in range(_ENCRYPT_RANDOM_BYTES_PARAMETER_CHUNK_COUNT)
            ]
        )
    ]


_test_scoped_encryption_key: Optional[bytes] = None
_last_encryption_test_name: Optional[str] = None

_test_seeded_data: Optional[bytes] = None
_last_seeded_data_test_name: Optional[str] = None


# TODO: v
# TODO: v
# TODO: v
# TODO: (make an issue for this) some Python tests have now been replaced by tests in the library
@pytest.fixture
def encryption_key(request) -> bytes:
    global _test_scoped_encryption_key, _last_encryption_test_name
    if request.node.originalname != _last_encryption_test_name:
        random.seed(request.node.originalname)
        _test_scoped_encryption_key = quocofs.key(
            bytes.hex(random.randbytes(20)), random.randbytes(quocofs.SALT_LENGTH)
        )
        _last_encryption_test_name = request.node.originalname

    return _test_scoped_encryption_key


@pytest.fixture
def seeded_data(request) -> bytes:
    global _test_seeded_data, _last_seeded_data_test_name
    if request.node.originalname != _last_seeded_data_test_name:
        random.seed(request.node.originalname)
        _test_seeded_data = random.randbytes(_ENCRYPT_RANDOM_BYTES_SIZE)
        _last_seeded_data_test_name = request.node.originalname

    return _test_seeded_data


@pytest.mark.parametrize("data", _encrypt_random_bytes_params())
def test_encrypt_decrypt_random_bytes(data: bytes, encryption_key: bytes):
    """Encrypt and decrypt with random binary data around chunk boundaries and check against input."""
    assert quocofs.loads(quocofs.dumps(data, encryption_key), encryption_key) == data
    # quocofs.dumps(data, encryption_key)


def test_fail_decrypt_random_bytes_wrong_key(seeded_data: bytes, encryption_key: bytes):
    """Encrypt and decrypt with random binary data around chunk boundaries and check against input."""
    wrong_key = quocofs.key(
        bytes.hex(random.randbytes(20)), random.randbytes(quocofs.SALT_LENGTH)
    )

    with pytest.raises(quocofs.DecryptionError):
        quocofs.loads(quocofs.dumps(seeded_data, encryption_key), wrong_key)


# TODO: Figure out how to test this without running out of memory (maybe just do it in Rust?). This looks like
#  another warning that we shouldn't be routinely passing data back and forth between Python and Rust where we can help
#  it.

# def test_encrypt_file_max_size(encryption_key: bytes):
#     """Quoco a file of size MAX_FILE_SIZE bytes."""
#     # WARNING: This will allocate MAX_FILE_SIZE bytes in memory
#     data = b"\x00" * quocofs.MAX_FILE_SIZE
#
#     quocofs.dumps(data, encryption_key)
#
#
# def test_fail_encrypt_file_too_large(encryption_key: bytes):
#     """Quoco a file larger than MAX_FILE_SIZE bytes, expect an exception."""
#     # WARNING: This will allocate MAX_FILE_SIZE + 1 bytes in memory
#     data = b"\x00" * (quocofs.MAX_FILE_SIZE + 1)
#
#     quocofs.dumps(data, encryption_key)
