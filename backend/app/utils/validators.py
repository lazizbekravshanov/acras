"""Shared validation logic."""

import re

VALID_STREAM_TYPES = {"rtsp", "mjpeg", "hls", "http_image"}
VALID_STATUSES = {"active", "inactive", "error", "maintenance"}
VALID_SEVERITIES = {"minor", "moderate", "severe", "critical"}
VALID_INCIDENT_TYPES = {"crash", "stall", "debris", "fire", "wrong_way", "pedestrian", "weather_hazard", "unknown"}
VALID_INCIDENT_STATUSES = {"detected", "confirmed", "responding", "clearing", "resolved", "false_positive"}

US_STATE_CODES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC",
}

INTERSTATE_PATTERN = re.compile(r"^I-\d{1,3}$")


def validate_stream_type(value: str) -> bool:
    return value in VALID_STREAM_TYPES


def validate_state_code(value: str) -> bool:
    return value.upper() in US_STATE_CODES


def validate_interstate(value: str) -> bool:
    return bool(INTERSTATE_PATTERN.match(value))


def validate_severity(value: str) -> bool:
    return value in VALID_SEVERITIES
