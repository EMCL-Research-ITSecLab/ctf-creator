import pytest
from src.pyyaml_functions import extract_hosts


def test_valid_cases():
    hosts = ["user1@10.20.30.40", "admin@192.168.1.1"]
    expected = ["10.20.30.40", "192.168.1.1"]
    assert extract_hosts(hosts) == expected


def test_missing_at_symbol():
    hosts = ["user1-10.20.30.40", "admin-192.168.1.1"]
    with pytest.raises(
        ValueError, match="Host string must contain exactly one '@' symbol"
    ):
        extract_hosts(hosts)


def test_empty_string():
    hosts = [""]
    with pytest.raises(ValueError, match="Host string cannot be empty"):
        extract_hosts(hosts)


def test_multiple_at_symbols():
    hosts = ["user1@subdomain@10.20.30.40", "admin@domain@192.168.1.1"]
    with pytest.raises(
        ValueError, match="Host string must contain exactly one '@' symbol"
    ):
        extract_hosts(hosts)


def test_mixed_valid_and_invalid():
    hosts = ["user1@10.20.30.40", "invalid@domain@10.20.30.40", ""]
    with pytest.raises(
        ValueError, match="Host string must contain exactly one '@' symbol"
    ):
        extract_hosts(hosts)
