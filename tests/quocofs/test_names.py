import random

import pytest
import quocofs

_NAMES_VALID_DATA = {
    b"\x9bs*\x7f:0)\x14J\xca6\xf1\x8c6\xc6-": "test_name_1",
    b"\xbf\xc3!!\xb0V&\x13\x87\xe3_\xf4\xde\xd3\xbfU": "another name with spaces",
    b"n2\x9cS\x82Wpt\xc2a\x1a\xa3\x1c\xbd*Y": "handling😀utf-8يَّcharacters",
    b"\xa8\x91\xff\xd9\x87n1#\xc0$\xdb\x00\x04D\xd1 ": "prematurely\x00null\x00terminated\x00",
}

_NAMES_VALID_DATA_CLEANED = {
    b"\x9bs*\x7f:0)\x14J\xca6\xf1\x8c6\xc6-": "test_name_1",
    b"\xbf\xc3!!\xb0V&\x13\x87\xe3_\xf4\xde\xd3\xbfU": "another name with spaces",
    b"n2\x9cS\x82Wpt\xc2a\x1a\xa3\x1c\xbd*Y": "handlingutf-8characters",
    b"\xa8\x91\xff\xd9\x87n1#\xc0$\xdb\x00\x04D\xd1 ": "prematurelynullterminated",
}

# TODO: Fix this incomprehensible word soup
_NAMES_INVALID_UUID_LENGTH_DATA_PARAMS = [
    pytest.param(data, id=id)
    for data, id in [
        (
            {
                b"": "look! nothing.",
            },
            "empty",
        ),
        (
            {
                b"\xb2\xe1P/\x80\xc8\x1e\xb6#r\x1d6\x8b\x18$\x86\xd2b@\x91)\xf9UZr\xdbI\xa4\x8a": "invalidly long uuid",
            },
            "too long",
        ),
        (
            {
                b"\xef": "just one little lonely byte",
            },
            "1 byte",
        ),
        (
            {
                b"\x9bs*\x7f:0)\x14J\xca6\xf1\x8c6\xc6-": "this first one is actually the correct length",
                b"0)\x14J\xca6\xf1\x8c6\xc6-": "but I want to make sure it picks up subsequent errors correctly",
            },
            "first correct, second too short",
        ),
    ]
]


_NAMES_EMPTY_NAME_DATA = {b"\x9bs*\x7f:0)\x14J\xca6\xf1\x8c6\xc6-": ""}

_NAMES_NAME_TOO_LONG_DATA = {
    b"\x9bs*\x7f:0)\x14J\xca6\xf1\x8c6\xc6-": bytes.hex(
        random.randbytes(quocofs.MAX_NAME_LENGTH // 2)
    )
    + "r"
}


@pytest.mark.skip(reason="names format de/serialization API isn't publicly visible")
def test_serialize_deserialize_valid_names():
    """Check serialized then deserialized names data against input."""
    assert (
        quocofs.deserialize_names(quocofs.serialize_names(_NAMES_VALID_DATA))
        == _NAMES_VALID_DATA_CLEANED
    )


@pytest.mark.skip(reason="names format de/serialization API isn't publicly visible")
def test_fail_deserialize_invalid_names():
    """Check serialized then deserialized names data against input."""
    assert quocofs.deserialize_names(quocofs.serialize_names(_NAMES_VALID_DATA))


@pytest.mark.skip(reason="names format de/serialization API isn't publicly visible")
@pytest.mark.parametrize("names", _NAMES_INVALID_UUID_LENGTH_DATA_PARAMS)
def test_fail_serialize_invalid_uuid_length(names):
    """Verify that an error is thrown when attempting to serialize a name entry with an invalid UUID length."""
    # TODO: Create better error messages for this
    with pytest.raises(BufferError):
        quocofs.serialize_names(names)


@pytest.mark.skip(reason="names format de/serialization API isn't publicly visible")
def test_fail_serialize_name_empty():
    """Verify that an error is thrown when attempting to serialize a name entry with an empty name."""
    with pytest.raises(ValueError):
        quocofs.serialize_names(_NAMES_EMPTY_NAME_DATA)


@pytest.mark.skip(reason="names format de/serialization API isn't publicly visible")
def test_fail_serialize_name_too_long():
    """Verify that an error is thrown when attempting to serialize a name entry that is greater than MAX_NAME_LENGTH."""
    with pytest.raises(ValueError):
        quocofs.serialize_names(_NAMES_NAME_TOO_LONG_DATA)
