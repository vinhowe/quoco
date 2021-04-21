import random

import pytest
import quocofs

_HASHES_VALID_DATA = {
    b"\x9bs*\x7f:0)\x14J\xca6\xf1\x8c6\xc6-": b"H\x11\x03\xe8(\x8e\xb9\xa7\xc9\xb0VEo\x90Y\x8ax\xbe\x94\xca11\xf2\xb0\xee\xfd\x9dK\x00\xe7\xffC",
    b"\xbf\xc3!!\xb0V&\x13\x87\xe3_\xf4\xde\xd3\xbfU": b'\xdfxh5\x8c\xe1h\xe4a\xef\x81\x06\xc2;2"\x12l\x1d\xc21\xda\xa1\xd7\xd1z\xa5\xb4nD\xd3\xb9',
    b"n2\x9cS\x82Wpt\xc2a\x1a\xa3\x1c\xbd*Y": b'\x98\xa1YB}\xbc~\xce{6^"k\xcbgU\xcct\xc8[\xf5B\xa6wO\xcf]\x97\x85=t\xdb',
}


# TODO: Fix this incomprehensible word soup
_HASHES_INVALID_UUID_LENGTH_DATA_PARAMS = [
    pytest.param(data, id=id)
    for data, id in [
        (
            {
                b"": b"H\x11\x03\xe8(\x8e\xb9\xa7\xc9\xb0VEo\x90Y\x8ax\xbe\x94\xca11\xf2\xb0\xee\xfd\x9dK\x00\xe7\xffC"
            },
            "empty",
        ),
        (
            {
                b"\xb2\xe1P/\x80\xc8\x1e\xb6#r\x1d6\x8b\x18$\x86\xd2b@\x91)\xf9UZr\xdbI\xa4\x8a": b"H\x11\x03\xe8(\x8e\xb9\xa7\xc9\xb0VEo\x90Y\x8ax\xbe\x94\xca11\xf2\xb0\xee\xfd\x9dK\x00\xe7\xffC",
            },
            "too long",
        ),
        (
            {
                b"\xef": b"H\x11\x03\xe8(\x8e\xb9\xa7\xc9\xb0VEo\x90Y\x8ax\xbe\x94\xca11\xf2\xb0\xee\xfd\x9dK\x00\xe7\xffC",
            },
            "1 byte",
        ),
        (
            {
                b"\x9bs*\x7f:0)\x14J\xca6\xf1\x8c6\xc6-": b"H\x11\x03\xe8(\x8e\xb9\xa7\xc9\xb0VEo\x90Y\x8ax\xbe\x94\xca11\xf2\xb0\xee\xfd\x9dK\x00\xe7\xffC",
                b"0)\x14J\xca6\xf1\x8c6\xc6-": b"H\x11\x03\xe8(\x8e\xb9\xa7\xc9\xb0VEo\x90Y\x8ax\xbe\x94\xca11\xf2\xb0\xee\xfd\x9dK\x00\xe7\xffC",
            },
            "first correct, second too short",
        ),
    ]
]

# TODO: Fix this incomprehensible word soup
_HASHES_INVALID_HASH_LENGTH_DATA_PARAMS = [
    pytest.param(data, id=id)
    for data, id in [
        (
            {b"\x9bs*\x7f:0)\x14J\xca6\xf1\x8c6\xc6-": b""},
            "empty",
        ),
        (
            {
                b"\x9bs*\x7f:0)\x14J\xca6\xf1\x8c6\xc6-": b'R\xb9\x11\x96\x08\xc1m\xed\xb3\xe7\xf1\x82\xf3"l\xed\xadU\xe18\xe5f\x89\xfd\xf8\xb8_~)\xe2\x032Dv\xadV!9\xcb<\x16\xe6'
            },
            "too long",
        ),
        (
            {b"\x9bs*\x7f:0)\x14J\xca6\xf1\x8c6\xc6-": b"\xef"},
            "1 byte",
        ),
        (
            {
                b"\x9bs*\x7f:0)\x14J\xca6\xf1\x8c6\xc6-": b"H\x11\x03\xe8(\x8e\xb9\xa7\xc9\xb0VEo\x90Y\x8ax\xbe\x94\xca11\xf2\xb0\xee\xfd\x9dK\x00\xe7\xffC",
                b"\xbf\xc3!!\xb0V&\x13\x87\xe3_\xf4\xde\xd3\xbfU": b"0)\x14J\xca6\xf1\x8c6\xc6-",
            },
            "first correct, second too short",
        ),
    ]
]


@pytest.mark.skip(reason="hashes format de/serialization API isn't currently visible")
def test_serialize_deserialize_valid_hashes():
    """Check serialized then deserialized hashes data against input."""
    data = quocofs.serialize_hashes(_HASHES_VALID_DATA)
    assert (
        quocofs.deserialize_hashes(quocofs.serialize_hashes(_HASHES_VALID_DATA))
        == _HASHES_VALID_DATA
    )


@pytest.mark.skip(reason="hashes format de/serialization API isn't currently visible")
@pytest.mark.parametrize("hashes", _HASHES_INVALID_UUID_LENGTH_DATA_PARAMS)
def test_fail_serialize_invalid_uuid_length(hashes):
    """Verify that an error is thrown when attempting to serialize a hash entry with an invalid UUID length."""
    # TODO: Create better error messages for this. It looks like this will probably require making a Python module for
    #  data validation on top of quocofs as it exists now
    with pytest.raises(BufferError):
        quocofs.serialize_hashes(hashes)


@pytest.mark.skip(reason="hashes format de/serialization API isn't currently visible")
@pytest.mark.parametrize("hashes", _HASHES_INVALID_HASH_LENGTH_DATA_PARAMS)
def test_fail_serialize_invalid_hash_length(hashes):
    """Verify that an error is thrown when attempting to serialize a hash entry with an invalid UUID length."""
    # TODO: Create better error messages for this
    with pytest.raises(BufferError):
        quocofs.serialize_hashes(hashes)
