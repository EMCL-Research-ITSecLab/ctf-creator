import pytest
from unittest.mock import mock_open, patch, MagicMock
from src.ovpn_helper_functions import modify_ovpn_file, RemoteLineNotFoundError


@patch("os.path.exists", return_value=True)
@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="remote 10.0.0.1 1194\nsome other line\n",
)
def test_modify_ovpn_file_success(mock_file, mock_exists):
    # Arrange
    file_path = "/mock/path/client.ovpn"
    new_port = 8080
    new_route_ip = "192.168.1.1"

    # Act
    modify_ovpn_file(file_path, new_port, new_route_ip)

    # Assert
    mock_exists.assert_called_once_with(file_path)
    handle = mock_file()

    # Ensure file was opened for reading and writing
    mock_file.assert_any_call(file_path, "r")
    mock_file.assert_any_call(file_path, "w")

    # Check if the right modifications were made
    expected_output = [
        "remote 10.0.0.1 8080\n",
        "route-nopull\n",
        "route 192.168.1.1\n",
        'pull-filter ignore "redirect-gateway"\n',
        'pull-filter ignore "dhcp-option"\n',
        'pull-filter ignore "route"\n',
        "some other line\n",
    ]
    handle.writelines.assert_called_once_with(expected_output)


@patch("os.path.exists", return_value=False)
@patch("builtins.open", new_callable=mock_open)
def test_modify_ovpn_file_file_not_exist(mock_file, mock_exists):
    # Arrange
    file_path = "/mock/path/nonexistent.ovpn"
    new_port = 8080
    new_route_ip = "192.168.1.1"

    # Act
    modify_ovpn_file(file_path, new_port, new_route_ip)

    # Assert
    mock_exists.assert_called_once_with(file_path)
    mock_file.assert_not_called()  # File should not be opened if it doesn't exist


@patch("os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data="some other line\n")
def test_modify_ovpn_file_no_remote_line_raises_error(mock_file, mock_exists):
    # Arrange
    file_path = "/mock/path/client.ovpn"
    new_port = 8080
    new_route_ip = "192.168.1.1"

    # Act & Assert
    with pytest.raises(
        RemoteLineNotFoundError, match="No 'remote' line found in the file."
    ):
        modify_ovpn_file(file_path, new_port, new_route_ip)

    # Ensure file was opened for reading
    mock_file.assert_called_with(file_path, "r")
    mock_file.assert_called_once()
