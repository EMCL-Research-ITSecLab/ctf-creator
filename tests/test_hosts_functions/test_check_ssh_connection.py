import pytest
from unittest.mock import patch
import sys
import subprocess
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)

from src.hosts_functions import check_ssh_connection


@patch("src.hosts_functions.subprocess.run")
def test_check_ssh_connection_success(mock_subprocess):
    mock_subprocess.return_value.returncode = 0  # Simulate successful SSH

    assert check_ssh_connection("user@192.168.1.1") == True


@patch("src.hosts_functions.subprocess.run")
def test_check_ssh_connection_failure(mock_subprocess):
    mock_subprocess.return_value.returncode = 1
    mock_subprocess.return_value.stderr = "Permission denied"

    assert check_ssh_connection("user@192.168.1.1") == False


@patch("src.hosts_functions.subprocess.run")
def test_check_ssh_connection_timeout(mock_subprocess):
    mock_subprocess.side_effect = subprocess.TimeoutExpired(cmd="ssh", timeout=10)

    assert check_ssh_connection("user@192.168.1.1") == False


@patch("src.hosts_functions.subprocess.run")
def test_check_ssh_connection_exception(mock_subprocess):
    mock_subprocess.side_effect = Exception("SSH failed")

    assert check_ssh_connection("user@192.168.1.1") == False
