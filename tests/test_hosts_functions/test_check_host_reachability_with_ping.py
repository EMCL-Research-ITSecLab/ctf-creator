import pytest
from unittest.mock import patch, MagicMock
import subprocess
import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)

from src.hosts_functions import check_host_reachability_with_ping

# Mocked data
reachable_host = "192.168.1.1"
unreachable_host = "192.168.1.2"


@patch("src.hosts_functions.subprocess.run")
@patch("src.hosts_functions.sys.exit")
def test_check_host_reachability_with_ping_all_reachable(mock_exit, mock_subprocess):
    mock_subprocess.return_value.returncode = 0  # Simulate ping success

    check_host_reachability_with_ping([reachable_host])

    # Assert that sys.exit was not called, meaning no hosts were unreachable
    mock_exit.assert_not_called()


@patch("src.hosts_functions.subprocess.run")
@patch("src.hosts_functions.sys.exit")
def test_check_host_reachability_with_ping_some_unreachable(mock_exit, mock_subprocess):
    mock_subprocess.side_effect = [
        MagicMock(returncode=0),  # First host is reachable
        MagicMock(returncode=1),  # Second host is unreachable
    ]

    check_host_reachability_with_ping([reachable_host, unreachable_host])

    # Assert that sys.exit was called with code 1 because one host was unreachable
    mock_exit.assert_called_once_with(1)


@patch("src.hosts_functions.subprocess.run")
@patch("src.hosts_functions.sys.exit")
def test_check_host_reachability_with_ping_exception(mock_exit, mock_subprocess):
    mock_subprocess.side_effect = Exception("Ping failed")

    check_host_reachability_with_ping([reachable_host])

    # Assert that sys.exit was called with code 1 because of an exception
    mock_exit.assert_called_once_with(1)
