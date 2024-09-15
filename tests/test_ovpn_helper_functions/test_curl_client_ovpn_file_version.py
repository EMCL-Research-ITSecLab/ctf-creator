import pytest
import subprocess
from unittest.mock import patch, MagicMock
from src.ovpn_helper_functions import (
    curl_client_ovpn_file_version,
    DownloadError,
)


@patch("subprocess.run")
@patch("os.makedirs")
@patch("time.sleep", return_value=None)  # Mock time.sleep to avoid actual waiting
def test_curl_client_ovpn_file_version_success(
    mock_sleep, mock_makedirs, mock_subprocess_run
):
    # Arrange
    host_address = "10.0.0.1"
    user_name = "test_user"
    counter = 1
    save_path = "/mock/path"

    # Simulate successful run of the curl command
    mock_subprocess_run.return_value = MagicMock()

    # Act
    curl_client_ovpn_file_version(host_address, user_name, counter, save_path)

    # Assert
    mock_makedirs.assert_called_once_with(
        f"{save_path}/data/{user_name}", exist_ok=True
    )
    expected_command = f"curl -o {save_path}/data/{user_name}/client.ovpn http://{host_address}:{80 + counter}/client.ovpn"
    mock_subprocess_run.assert_called_once_with(
        expected_command, shell=True, check=True
    )
    mock_sleep.assert_not_called()  # No retries should occur on success


@patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "curl"))
@patch("os.makedirs")
@patch("time.sleep", return_value=None)  # Mock time.sleep to avoid actual waiting
def test_curl_client_ovpn_file_version_retry(
    mock_sleep, mock_makedirs, mock_subprocess_run
):
    # Arrange
    host_address = "10.0.0.1"
    user_name = "test_user"
    counter = 1
    save_path = "/mock/path"
    max_retries = 3

    # Act
    with pytest.raises(DownloadError, match="Max retries exceeded."):
        curl_client_ovpn_file_version(
            host_address, user_name, counter, save_path, max_retries=max_retries
        )

    # Assert
    mock_makedirs.assert_called_once_with(
        f"{save_path}/data/{user_name}", exist_ok=True
    )
    expected_command = f"curl -o {save_path}/data/{user_name}/client.ovpn http://{host_address}:{80 + counter}/client.ovpn"
    assert mock_subprocess_run.call_count == max_retries  # Ensure retries occurred
    mock_sleep.assert_called_with(3)  # Ensure sleep was called for retrying


@patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "curl"))
@patch("os.makedirs", side_effect=OSError("Mocked makedirs error"))
@patch("time.sleep", return_value=None)  # Mock time.sleep to avoid actual waiting
def test_curl_client_ovpn_file_version_oserror(
    mock_sleep, mock_makedirs, mock_subprocess_run
):
    # Arrange
    host_address = "10.0.0.1"
    user_name = "test_user"
    counter = 1
    save_path = "/mock/path"

    # Act & Assert
    with pytest.raises(DownloadError, match="An unexpected error occurred"):
        curl_client_ovpn_file_version(host_address, user_name, counter, save_path)

    # Assert
    mock_makedirs.assert_called_once_with(
        f"{save_path}/data/{user_name}", exist_ok=True
    )
    mock_subprocess_run.assert_not_called()  # Should not reach the curl command
    mock_sleep.assert_not_called()  # No retries should occur because of the early failure


@patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "curl"))
@patch("os.makedirs")
@patch("time.sleep", return_value=None)  # Mock time.sleep to avoid actual waiting
def test_curl_client_ovpn_file_version_max_retries(
    mock_sleep, mock_makedirs, mock_subprocess_run
):
    # Arrange
    host_address = "10.0.0.1"
    user_name = "test_user"
    counter = 1
    save_path = "/mock/path"
    max_retries = 5  # Set maximum retries

    # Act
    with pytest.raises(DownloadError, match="Max retries exceeded."):
        curl_client_ovpn_file_version(
            host_address, user_name, counter, save_path, max_retries=max_retries
        )

    # Assert
    mock_makedirs.assert_called_once_with(
        f"{save_path}/data/{user_name}", exist_ok=True
    )
    expected_command = f"curl -o {save_path}/data/{user_name}/client.ovpn http://{host_address}:{80 + counter}/client.ovpn"
    assert (
        mock_subprocess_run.call_count == max_retries
    )  # Should retry max_retries times
    assert (
        mock_sleep.call_count == max_retries
    )  # Ensure sleep was called after each retry
