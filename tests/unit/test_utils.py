from dataclasses import asdict

import pytest
import werkzeug.exceptions

from src.utils import (
    convert_bytes,
    normpath,
    http_response,
    abort_with,
)


def test_convert_bytes():
    assert convert_bytes(0, suffix="b") == "0 b"
    assert convert_bytes(1024, suffix="b") == "1 Kb"
    assert convert_bytes(1024**2, suffix="b") == "1 Mb"
    assert convert_bytes(1024**3, suffix="b") == "1 Gb"
    assert convert_bytes(1024**4, suffix="b") == "1 Tb"
    assert convert_bytes(1024**5, suffix="b") == "1 Pb"
    assert convert_bytes(1024**6, suffix="b") == "1 Eb"
    assert convert_bytes(1024**7, suffix="b") == "1 Zb"
    assert convert_bytes(1024**8, suffix="b") == "1 Yb"
    assert convert_bytes(10, suffix="B") == "10 B"
    assert convert_bytes(1024, suffix="iB") == "1 KiB"


def test_normpath():
    assert normpath("/tmp") == "/tmp"
    assert normpath("//tmp") == "/tmp"
    assert normpath("///tmp") == "/tmp"
    assert normpath("tmp") == "/tmp"
    assert normpath("/tmp/") == "/tmp"
    assert normpath("tmp/") == "/tmp"
    assert normpath("//tmp//") == "/tmp"


def test_response():
    assert http_response(code=200, message="test") == {
        "code": 200,
        "reason": "OK",
        "message": "test",
    }
    assert asdict(http_response(code=400, message="error", serialize=False)) == {
        "code": 400,
        "reason": "Bad Request",
        "message": "error",
    }


def test_abort_with():
    with pytest.raises(werkzeug.exceptions.BadRequest) as ex:
        assert abort_with(code=400, message="custom message")
    assert ex.value.code == 400
    assert ex.value.data == {
        "code": 400,
        "reason": "Bad Request",
        "message": "custom message",
    }
    with pytest.raises(werkzeug.exceptions.Unauthorized) as ex:
        assert abort_with(code=401, message="custom message")
    assert ex.value.code == 401
    assert ex.value.data == {
        "code": 401,
        "reason": "Unauthorized",
        "message": "custom message",
    }
    with pytest.raises(werkzeug.exceptions.Forbidden) as ex:
        assert abort_with(code=403, message="custom message")
    assert ex.value.code == 403
    assert ex.value.data == {
        "code": 403,
        "reason": "Forbidden",
        "message": "custom message",
    }
