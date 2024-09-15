import pytest
from unittest.mock import mock_open, patch
from src.ovpn_helper_functions import (
    modify_ovpn_file_change_host,
    RemoteLineNotFoundError,
)


@patch("os.path.exists", return_value=True)
@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="remote 10.0.0.1 1194\nsome other line\n",
)
def test_modify_ovpn_file_change_host_change_needed(mock_file, mock_exists):
    # Arrange
    file_path = "/mock/path/client.ovpn"
    new_ip = "192.168.1.1"
    new_port = 8080
    username = "testuser"

    # Act
    result = modify_ovpn_file_change_host(file_path, new_ip, new_port, username)

    # Assert
    mock_exists.assert_called_once_with(file_path)
    mock_file.assert_called_with(file_path, "r")  # Check if file was opened for reading
    mock_file().write.assert_called_once()  # Check if the file was opened for writing
    assert result == username  # Ensure the username is returned if changes are made


@patch("os.path.exists", return_value=True)
@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="remote 10.0.0.1 1194\nsome other line\n",
)
def test_modify_ovpn_file_change_host_change_needed(mock_file, mock_exists):
    # Arrange
    file_path = "/mock/path/client.ovpn"
    new_ip = "192.168.1.1"
    new_port = 8080
    username = "testuser"

    # Act
    result = modify_ovpn_file_change_host(file_path, new_ip, new_port, username)

    # Assert
    mock_exists.assert_called_once_with(file_path)

    # Ensure the file was first opened for reading
    mock_file.assert_any_call(file_path, "r")

    # Ensure the file was later opened for writing
    mock_file.assert_any_call(file_path, "w")

    # Ensure the file was actually written to
    handle = mock_file()
    handle.writelines.assert_called_once()

    assert result == username  # Ensure the username is returned if changes are made


@patch("os.path.exists", return_value=False)
def test_modify_ovpn_file_change_host_file_does_not_exist(mock_exists):
    # Arrange
    file_path = "/mock/path/client.ovpn"
    new_ip = "192.168.1.1"
    new_port = 8080
    username = "testuser"

    # Act
    result = modify_ovpn_file_change_host(file_path, new_ip, new_port, username)

    # Assert
    mock_exists.assert_called_once_with(file_path)
    assert result is None  # If the file doesn't exist, the function should return None


@patch("os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data="some other line\n")
def test_modify_ovpn_file_change_host_no_remote_line(mock_file, mock_exists):
    # Arrange
    file_path = "/mock/path/client.ovpn"
    new_ip = "192.168.1.1"
    new_port = 8080
    username = "testuser"

    # Act & Assert
    with pytest.raises(
        RemoteLineNotFoundError, match="No 'remote' line found in the file."
    ):
        modify_ovpn_file_change_host(file_path, new_ip, new_port, username)

    mock_exists.assert_called_once_with(file_path)
    mock_file.assert_called_with(file_path, "r")  # Ensure file was opened for reading
