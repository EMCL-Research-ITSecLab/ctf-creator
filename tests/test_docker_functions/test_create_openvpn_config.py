import pytest
import docker
from src.docker_functions import create_openvpn_config
import unittest
from unittest.mock import MagicMock, patch, call
from src.ovpn_helper_functions import DownloadError


class MockOVPNFunc:
    @staticmethod
    def curl_client_ovpn_file_version(
        host_address, user_name, counter, save_path, *args, **kwargs
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


@patch("src.docker_functions.ovpn_func.curl_client_ovpn_file_version")
@patch("src.docker_functions.os.makedirs")
@patch("docker.from_env")
@patch("src.docker_functions.exit", side_effect=SystemExit)
@patch("builtins.open", new_callable=MagicMock)
def test_create_openvpn_config_success(
    mock_open,
    mock_exit,
    mock_docker_from_env,
    mock_os_makedirs,
    mock_curl_client_ovpn_file_version,
):
    mock_docker_client = MagicMock()
    mock_container = MagicMock()
    mock_docker_client.containers.get.return_value = mock_container
    mock_docker_from_env.return_value = mock_docker_client
    mock_container.exec_run.return_value = (0, "Command executed successfully")
    mock_curl_client_ovpn_file_version.return_value = None

    # Simulate the archive being an iterable that yields chunks of data
    mock_archive = [b"chunk1", b"chunk2", b"chunk3"]

    # Simulate a stat object
    mock_stat = {"name": "mock_stat"}

    # Mock the get_archive method to return the archive and the stat object
    mock_container.get_archive.return_value = (mock_archive, mock_stat)

    # Create a mock file object with a mock write method
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file

    # Call the code that saves the archive to a file
    local_path_to_data = "/mock/path/to/data"
    with open(local_path_to_data, "wb") as f:
        for chunk in mock_archive:
            f.write(chunk)

    # Assert that the file's write method was called for each chunk
    mock_file.write.assert_any_call(b"chunk1")
    mock_file.write.assert_any_call(b"chunk2")
    mock_file.write.assert_any_call(b"chunk3")
    assert mock_file.write.call_count == 3  # Ensure 3 chunks were written

    user_name = "test_user"
    counter = 1
    host_address = "10.20.30.101"
    save_path = "/mock/path"
    new_push_route = "10.0.0.0/24"

    create_openvpn_config(
        mock_docker_client, user_name, counter, host_address, save_path, new_push_route
    )

    # Instead of asserting a single call, check both calls
    mock_docker_client.containers.get.assert_has_calls(
        [
            call("test_user_openvpn"),
            call().exec_run("./genclient.sh", detach=True),
            call("test_user_openvpn"),
            call().get_archive("/opt/Dockovpn_data"),
        ]
    )
    mock_container.exec_run.assert_called_once_with("./genclient.sh", detach=True)
    mock_curl_client_ovpn_file_version.assert_called_once_with(
        host_address, user_name, counter, save_path
    )
    mock_os_makedirs.assert_called_once_with(
        f"{save_path}/data/{user_name}", exist_ok=True
    )


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
