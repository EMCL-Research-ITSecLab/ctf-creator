import pytest
import subprocess
import os
from unittest.mock import patch, mock_open, MagicMock
import time
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
import os
import subprocess
import time
from unittest.mock import patch, Mock

# Custom Exception
class DownloadError(Exception):
    pass

from src.ovpn_helper_functions import DownloadError, curl_client_ovpn_file_version
# # Sample parameters for testing
# container = MagicMock()
# host_address = "127.0.0.1"
# user_name = "testuser"
# counter = 5
# save_path = "/tmp/test_ovpn"
# url = f"http://{host_address}:{80 + counter}/client.ovpn"


# @pytest.fixture
# def setup_teardown():
#     """Setup and teardown to ensure clean testing environment."""
#     yield
#     # Teardown: Remove the created directory after tests
#     if os.path.exists(save_path):
#         os.system(f'rm -rf {save_path}')

# def test_curl_client_ovpn_file_version_success(setup_teardown):
#     with patch('os.makedirs') as mock_makedirs, \
#          patch('subprocess.run') as mock_subprocess:
        
#         # Simulate successful file download
#         mock_subprocess.return_value = None
        
#         curl_client_ovpn_file_version(container, host_address, user_name, counter, save_path)
        
#         # Ensure directory creation was attempted
#         mock_makedirs.assert_called_once_with(f"{save_path}/data/{user_name}", exist_ok=True)
        
#         # Ensure subprocess was called with correct command
#         mock_subprocess.assert_called_once_with(f"curl -o {save_path}/data/{user_name}/client.ovpn {url}", shell=True, check=True
# )


# def test_curl_client_ovpn_file_version_failure_retry():
#     with patch('os.makedirs'), \
#          patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'curl')), \
#          patch('time.sleep') as mock_sleep, \
#          patch('builtins.print') as mock_print:

#         with pytest.raises(DownloadError, match="Max retries exceeded."):
#             curl_client_ovpn_file_version(None, "127.0.0.1", "testuser", 5, "/tmp/test_ovpn", max_retries_counter=0, max_retries=3)

#         # Verify that the function attempted to download multiple times
#         assert mock_sleep.call_count == 3  # Ensuring retries happened
#         assert mock_print.call_count > 3   # Print statements should show retries


# # def test_curl_client_ovpn_file_version_unexpected_error():
# #     with patch('os.makedirs'), \
# #          patch('subprocess.run', side_effect=Exception("Unexpected error")), \
# #          patch('time.sleep') as mock_sleep, \
# #          patch('builtins.print') as mock_print:
        
# #         with pytest.raises(SystemExit):
# #             curl_client_ovpn_file_version(None, "127.0.0.1", "testuser", 5, "/tmp/test_ovpn", max_retries_counter=0, max_retries=3)
        
# #         mock_print.assert_any_call("Unexpected error: Unexpected error")

# def test_curl_client_ovpn_file_version_unexpected_error():
#     with patch('os.makedirs'), \
#          patch('subprocess.run', side_effect=Exception("Unexpected error")), \
#          patch('time.sleep'), \
#          patch('builtins.print') as mock_print:

#         with pytest.raises(DownloadError, match="An unexpected error occurred - Unexpected error"):
#             curl_client_ovpn_file_version(None, "127.0.0.1", "testuser", 5, "/tmp/test_ovpn", max_retries_counter=0, max_retries=3)

#     mock_print.assert_any_call("Error: An unexpected error occurred - Unexpected error")

# Test function for a successful download
@patch('os.makedirs')
@patch('subprocess.run')
@patch('time.sleep', return_value=None)
def test_curl_client_ovpn_file_version_successful(mock_sleep, mock_run, mock_makedirs):
    container = 'container:latest'
    host_address = '127.0.0.1'
    user_name = 'testuser'
    counter = 1
    save_path = '/fake/path'

    mock_run.return_value = Mock()

    curl_client_ovpn_file_version(container, host_address, user_name, counter, save_path)

    save_directory = f"{save_path}/data/{user_name}"
    url = f"http://{host_address}:{80 + counter}/client.ovpn"
    command = f"curl -o {save_directory}/client.ovpn {url}"

    mock_makedirs.assert_called_once_with(save_directory, exist_ok=True)
    mock_run.assert_called_once_with(command, shell=True, check=True)
    mock_sleep.assert_not_called()

# Test function for the retry mechanism
@patch('os.makedirs')
@patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'curl'))
@patch('time.sleep', return_value=None)
def test_curl_client_ovpn_file_version_retry_mechanism(mock_sleep, mock_run, mock_makedirs):
    container = 'container'
    host_address = '127.0.0.1'
    user_name = 'testuser'
    counter = 1
    save_path = '/fake/path'
    max_retries_counter = 0
    max_retries = 3

    try:
        curl_client_ovpn_file_version(container, host_address, user_name, counter, save_path, max_retries_counter, max_retries)
    except DownloadError:
        pass

    save_directory = f"{save_path}/data/{user_name}"
    url = f"http://{host_address}:{80 + counter}/client.ovpn"
    command = f"curl -o {save_directory}/client.ovpn {url}"

    mock_makedirs.assert_called_once_with(save_directory, exist_ok=True)
    assert mock_run.call_count == max_retries
    assert mock_sleep.call_count == max_retries

# Test function for unexpected error in os.makedirs
@patch('os.makedirs', side_effect=Exception('Unexpected error in makedirs'))
def test_curl_client_ovpn_file_version_unexpected_error_in_makedirs(mock_makedirs):
    container = 'container'
    host_address = '127.0.0.1'
    user_name = 'testuser'
    counter = 1
    save_path = '/fake/path'

    try:
        curl_client_ovpn_file_version(container, host_address, user_name, counter, save_path)
    except DownloadError as e:
        assert str(e) == "An unexpected error occurred - Unexpected error in makedirs"

    mock_makedirs.assert_called_once_with(f"{save_path}/data/{user_name}", exist_ok=True)

# Test function for unexpected error in subprocess.run
@patch('os.makedirs')
@patch('subprocess.run', side_effect=Exception('Unexpected error in run'))
@patch('time.sleep', return_value=None)
def test_curl_client_ovpn_file_version_unexpected_error_in_run(mock_sleep, mock_run, mock_makedirs):
    container = 'container'
    host_address = '127.0.0.1'
    user_name = 'testuser'
    counter = 1
    save_path = '/fake/path'
    max_retries_counter = 0
    max_retries = 3

    try:
        curl_client_ovpn_file_version(container, host_address, user_name, counter, save_path, max_retries_counter, max_retries)
    except DownloadError as e:
        assert "An unexpected error occurred" in str(e)

    assert mock_run.call_count == max_retries
    assert mock_sleep.call_count == max_retries
