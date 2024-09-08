import pytest
import unittest
from unittest.mock import patch, MagicMock
import docker
import os
import time
from src.docker_functions import create_openvpn_config
import unittest
from unittest.mock import MagicMock, patch
from src.docker_functions import create_openvpn_config  # Adjust import as needed


class MockOVPNFunc:
    @staticmethod
    def curl_client_ovpn_file_version(
        container, host_address, user_name, counter, save_path, *args, **kwargs
    ):
        # Mock implementation of curl_client_ovpn_file_version
        pass


@pytest.fixture
def mock_docker_client():
    with patch("docker.from_env") as mock_from_env:
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_from_env.return_value = mock_client
        mock_client.containers.get.return_value = mock_container
        mock_container.exec_run.return_value = (0, b"Success")
        # Simulate behavior, include get_archive if it's used
        mock_container.get_archive.return_value = (iter([b"archive_data"]), None)
        yield mock_client, mock_container


@pytest.fixture
def mock_os_makedirs():
    with patch("os.makedirs") as mock_makedirs:
        yield mock_makedirs


@pytest.fixture
def mock_ovpn_helper_functions():
    with patch(
        "src.ovpn_helper_functions.curl_client_ovpn_file_version",
        new_callable=lambda: MockOVPNFunc.curl_client_ovpn_file_version,
    ):
        yield


def test_create_openvpn_config_success(
    mock_docker_client, mock_os_makedirs, mock_ovpn_helper_functions
):
    mock_client, mock_container = mock_docker_client
    user_name = "test_user"
    counter = 1
    host_address = "10.20.30.101"
    save_path = "/mock/path"
    new_push_route = "10.0.0.0/24"

    with patch("builtins.open", unittest.mock.mock_open()) as mocked_open:
        with pytest.raises(SystemExit) as cm:
            create_openvpn_config(
                mock_client, user_name, counter, host_address, save_path, new_push_route
            )
        # Ensure SystemExit was raised with code 1
        assert cm.value.code == 1

    # Check if the container was fetched
    mock_client.containers.get.assert_called_once_with(f"{user_name}_openvpn")
    # Check if the command was run in the container
    mock_container.exec_run.assert_called_once_with("./genclient.sh", detach=True)
    # Check if the archive was retrieved if it is used in the implementation
    mock_container.get_archive.assert_called_once_with("/opt/Dockovpn_data")

    # Check if the file was saved correctly
    mocked_open.assert_called_once_with(
        f"{save_path}/data/{user_name}/dockovpn_data.tar", "wb"
    )
    # Check if the mock file write was called
    handle = mocked_open()
    handle.write.assert_called_with(b"archive_data")


@patch("docker.from_env")
def test_container_not_found(mock_from_env):
    # Set up mocks
    mock_client = MagicMock()
    mock_from_env.return_value = mock_client
    mock_client.containers.get.side_effect = docker.errors.NotFound(
        "Container not found"
    )

    user_name = "test_user"
    counter = 1
    host_address = "10.20.30.101"
    save_path = "/mock/path"
    new_push_route = "10.0.0.0/24"

    with pytest.raises(SystemExit):
        create_openvpn_config(
            mock_client, user_name, counter, host_address, save_path, new_push_route
        )


@patch("docker.from_env")
def test_command_execution_failure(mock_from_env):
    # Set up mocks
    mock_client = MagicMock()
    mock_container = MagicMock()
    mock_from_env.return_value = mock_client
    mock_client.containers.get.return_value = mock_container
    mock_container.exec_run.side_effect = Exception("Command execution failed")

    user_name = "test_user"
    counter = 1
    host_address = "http://example.com"
    save_path = "/mock/path"
    new_push_route = "10.0.0.0/24"

    with pytest.raises(SystemExit):
        create_openvpn_config(
            mock_client, user_name, counter, host_address, save_path, new_push_route
        )


@patch("docker.from_env")
def test_saving_archive_failure(mock_from_env):
    # Set up mocks
    mock_client = MagicMock()
    mock_container = MagicMock()
    mock_from_env.return_value = mock_client
    mock_client.containers.get.return_value = mock_container
    mock_container.exec_run.return_value = (0, b"Success")
    mock_container.get_archive.return_value = (
        iter([b"archive_data"]),
        None,
    )  # Simulate successful archive retrieval
    mock_container.get_archive.side_effect = Exception("Failed to get archive")

    user_name = "test_user"
    counter = 1
    host_address = "http://example.com"
    save_path = "/mock/path"
    new_push_route = "10.0.0.0/24"

    with pytest.raises(SystemExit):
        create_openvpn_config(
            mock_client, user_name, counter, host_address, save_path, new_push_route
        )
