"""Tests for validation utilities."""

from app.utils.validators import (
    validate_interstate,
    validate_severity,
    validate_state_code,
    validate_stream_type,
)


def test_valid_stream_types():
    assert validate_stream_type("rtsp") is True
    assert validate_stream_type("mjpeg") is True
    assert validate_stream_type("hls") is True
    assert validate_stream_type("http_image") is True
    assert validate_stream_type("invalid") is False


def test_valid_state_codes():
    assert validate_state_code("FL") is True
    assert validate_state_code("ca") is True  # Case insensitive
    assert validate_state_code("XX") is False


def test_valid_interstates():
    assert validate_interstate("I-95") is True
    assert validate_interstate("I-5") is True
    assert validate_interstate("I-405") is True
    assert validate_interstate("US-1") is False
    assert validate_interstate("highway") is False


def test_valid_severities():
    assert validate_severity("minor") is True
    assert validate_severity("critical") is True
    assert validate_severity("extreme") is False
