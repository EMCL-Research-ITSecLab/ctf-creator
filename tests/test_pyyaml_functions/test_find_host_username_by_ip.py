import pytest
from src.pyyaml_functions import find_host_username_by_ip


def test_valid_ip_lookup():
    hosts = ["user1@10.20.30.40", "admin@192.168.1.1"]
    assert find_host_username_by_ip(hosts, "10.20.30.40") == "user1"
    assert find_host_username_by_ip(hosts, "192.168.1.1") == "admin"


def test_ip_not_found():
    hosts = ["user1@10.20.30.40", "admin@192.168.1.1"]
    assert find_host_username_by_ip(hosts, "8.8.8.8") is None  # IP not found


def test_empty_host_list():
    hosts = []
    assert find_host_username_by_ip(hosts, "10.20.30.40") is None  # No hosts provided


def test_invalid_format_missing_at():
    hosts = ["user1-10.20.30.40", "admin-192.168.1.1"]
    with pytest.raises(
        ValueError, match="Host string must contain exactly one '@' symbol"
    ):
        find_host_username_by_ip(hosts, "10.20.30.40")


def test_invalid_format_multiple_at():
    hosts = ["user1@subdomain@10.20.30.40", "admin@domain@192.168.1.1"]
    with pytest.raises(
        ValueError, match="Host string must contain exactly one '@' symbol"
    ):
        find_host_username_by_ip(hosts, "10.20.30.40")


def test_username_for_ip_with_print_warning(capsys):
    hosts = ["user1@10.20.30.40", "admin@192.168.1.1"]
    assert find_host_username_by_ip(hosts, "8.8.8.8") is None
    captured = capsys.readouterr()
    assert (
        "Warning: The IP address 8.8.8.8 in the client.ovpn is not defined"
        in captured.out
    )
