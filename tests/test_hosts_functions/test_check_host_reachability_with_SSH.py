import pytest
from unittest.mock import patch
import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)
from src.hosts_functions import check_host_reachability_with_SSH


@patch("src.hosts_functions.check_ssh_connection")
@patch("src.hosts_functions.sys.exit")
def test_check_host_reachability_with_SSH_all_success(mock_exit, mock_check_ssh):
    mock_check_ssh.return_value = True

    check_host_reachability_with_SSH(["user@192.168.1.1", "user@192.168.1.2"])

    mock_exit.assert_not_called()


@patch("src.hosts_functions.check_ssh_connection")
@patch("src.hosts_functions.sys.exit")
def test_check_host_reachability_with_SSH_some_failure(mock_exit, mock_check_ssh):
    mock_check_ssh.side_effect = [True, False]

    check_host_reachability_with_SSH(["user@192.168.1.1", "user@192.168.1.2"])

    mock_exit.assert_called_once_with(1)
