import pytest
from src.pyyaml_functions import extract_host_usernames


def test_valid_cases():
    hosts = ['user1@10.20.30.40', 'admin@192.168.1.1']
    expected = ['user1', 'admin']
    assert extract_host_usernames(hosts) == expected

def test_empty_string():
    with pytest.raises(ValueError, match="Empty string provided in hosts list"):
        extract_host_usernames([''])

def test_multiple_at_symbols():
    with pytest.raises(ValueError, match="Invalid host format: 'user1@subdomain@10.20.30.40'"):
        extract_host_usernames(['user1@subdomain@10.20.30.40'])

def test_no_at_symbol():
    with pytest.raises(ValueError, match="Invalid host format: 'username'"):
        extract_host_usernames(['username'])

def test_mixed_valid_and_invalid():
    with pytest.raises(ValueError, match="Invalid host format: 'invalid@domain@10.20.30.40'"):
        extract_host_usernames(['user1@10.20.30.40', 'invalid@domain@10.20.30.40', ''])

def test_all_invalid():
    invalid_hosts = ['user1-10.20.30.40', '', 'user@domain@subdomain']
    for host in invalid_hosts:
        with pytest.raises(ValueError):
            extract_host_usernames([host])
