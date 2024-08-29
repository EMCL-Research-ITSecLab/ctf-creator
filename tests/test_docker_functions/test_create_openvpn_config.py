import pytest
from unittest.mock import patch, MagicMock, call
import docker.errors
from src.docker_functions import create_openvpn_config
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# # Mock for the Docker client
# @pytest.fixture
# def mock_docker_client():
#     return MagicMock()


# # def test_create_openvpn_config(mock_docker_client):

#     # mock_container = MagicMock()
#     # mock_docker_client.containers.get.return_value = mock_container
#     # mock_container.exec_run.return_value = (0, "Command executed")

#     # user_name = "test_user"
#     # counter = 1
#     # host_address = "192.168.1.1"
#     # save_path = "/save/path"
#     # new_push_route = "192.168.1.0/24"

#     # with patch("ovpn_helper_functions.curl_client_ovpn_file_version") as mock_curl:
#     #     create_openvpn_config(mock_docker_client, user_name, counter, host_address, save_path, new_push_route)

#     #     mock_docker_client.containers.get.assert_called_once_with(f"{user_name}_openvpn")
#     #     mock_container.exec_run.assert_called_once_with("./genclient.sh", detach=True)
#     #     mock_curl.assert_called_once_with(mock_container, host_address, user_name, counter, save_path)

# @pytest.fixture
# def mock_docker_client():
#     return MagicMock()

# def test_create_openvpn_config(mock_docker_client):
#     mock_container = MagicMock()
#     mock_docker_client.containers.get.return_value = mock_container
#     mock_container.exec_run.return_value = (0, "Command executed")

#     user_name = "test_user"
#     counter = 1
#     host_address = "192.168.1.1"
#     save_path = "/save/path"
#     new_push_route = "192.168.1.0/24"

#     with patch("ovpn_helper_functions.curl_client_ovpn_file_version") as mock_curl, \
#          patch("os.makedirs") as mock_makedirs:
#         # Mock the directory creation to avoid permission errors
#         mock_makedirs.return_value = None

#         # Replace exit with an exception for test purposes
#         with patch("sys.exit") as mock_exit:
#             create_openvpn_config(mock_docker_client, user_name, counter, host_address, save_path, new_push_route)
            
#             mock_docker_client.containers.get.assert_called_once_with(f"{user_name}_openvpn")
#             mock_container.exec_run.assert_called_once_with("./genclient.sh", detach=True)
#             mock_curl.assert_called_once_with(mock_container, host_address, user_name, counter, save_path)
#             mock_makedirs.assert_called_once_with(f"{save_path}/data/{user_name}", exist_ok=True)
#             mock_exit.assert_not_called()  # Ensure exit was not called


# @pytest.fixture
# def mock_docker_client():
#     return MagicMock()

# def test_create_openvpn_config(mock_docker_client):
#     mock_container = MagicMock()
#     mock_docker_client.containers.get.return_value = mock_container
#     mock_container.exec_run.return_value = (0, "Command executed")
#     mock_container.get_archive.return_value = (MagicMock(), MagicMock())  # Mock get_archive

#     user_name = "test_user"
#     counter = 1
#     host_address = "192.168.1.1"
#     save_path = "/save/path"
#     new_push_route = "192.168.1.0/24"

#     with patch("ovpn_helper_functions.curl_client_ovpn_file_version") as mock_curl, \
#          patch("os.makedirs") as mock_makedirs, \
#          patch("sys.exit") as mock_exit:
#         # Mock the directory creation to avoid permission errors
#         mock_makedirs.return_value = None

#         create_openvpn_config(mock_docker_client, user_name, counter, host_address, save_path, new_push_route)
        
#         mock_docker_client.containers.get.assert_called_once_with(f"{user_name}_openvpn")
#         mock_container.exec_run.assert_called_once_with("./genclient.sh", detach=True)
#         mock_curl.assert_called_once_with(mock_container, host_address, user_name, counter, save_path)
#         mock_makedirs.assert_called_once_with(f"{save_path}/data/{user_name}", exist_ok=True)
#         mock_exit.assert_not_called()  # Ensure exit was not called

# import pytest
# from unittest.mock import MagicMock, patch
# import os
# import time
# from src.docker_functions import create_openvpn_config

# @patch('docker.DockerClient')
# def test_create_openvpn_config(mock_docker_client):
#     mock_container = MagicMock()
#     mock_docker_client.containers.get.return_value = mock_container
#     mock_container.exec_run.return_value = (0, "Command executed")
#     mock_container.get_archive.return_value = (MagicMock(), MagicMock())  # Mock get_archive
    
#     user_name = "test_user"
#     counter = 1
#     host_address = "192.168.1.1"
#     save_path = "/save/path"
#     new_push_route = "192.168.1.0/24"

#     with patch("ovpn_helper_functions.curl_client_ovpn_file_version") as mock_curl, \
#          patch("os.makedirs") as mock_makedirs, \
#          patch("builtins.open", mock_open()) as mock_open, \
#          patch("sys.exit") as mock_exit:
#         # Mock the directory creation to avoid permission errors
#         mock_makedirs.return_value = None
#         mock_open.return_value = MagicMock()
        
#         create_openvpn_config(mock_docker_client, user_name, counter, host_address, save_path, new_push_route)
        
#         # Ensure that the correct path is used in the call
#         local_save_path = f"{save_path}/data/{user_name}"
#         local_path_to_data = f"{save_path}/data/{user_name}/dockovpn_data.tar"
#         mock_makedirs.assert_called_once_with(local_save_path, exist_ok=True)
#         mock_open.assert_called_once_with(local_path_to_data, "wb")

#         # Check if sys.exit was called (i.e., failure cases)
#         mock_exit.assert_not_called()

# import pytest
# from unittest.mock import MagicMock, mock_open, patch
# import os
# from src.docker_functions import create_openvpn_config

# @patch('docker.DockerClient')
# def test_create_openvpn_config(mock_docker_client):
#     mock_container = MagicMock()
#     mock_docker_client.containers.get.return_value = mock_container
#     mock_container.exec_run.return_value = (0, "Command executed")
#     mock_container.get_archive.return_value = (MagicMock(), MagicMock())  # Mock get_archive
    
#     user_name = "test_user"
#     counter = 1
#     host_address = "192.168.1.1"
#     save_path = "/save/path"
#     new_push_route = "192.168.1.0/24"

#     with patch("ovpn_helper_functions.curl_client_ovpn_file_version") as mock_curl, \
#          patch("os.makedirs") as mock_makedirs, \
#          patch("builtins.open", mock_open()) as mock_open, \
#          patch("sys.exit") as mock_exit:
#         # Mock the directory creation to avoid permission errors
#         mock_makedirs.return_value = None
#         mock_open.return_value = MagicMock()
        
#         create_openvpn_config(mock_docker_client, user_name, counter, host_address, save_path, new_push_route)
        
#         # Ensure that the correct path is used in the call
#         local_save_path = f"{save_path}/data/{user_name}"
#         local_path_to_data = f"{save_path}/data/{user_name}/dockovpn_data.tar"
#         mock_makedirs.assert_called_once_with(local_save_path, exist_ok=True)
#         mock_open.assert_called_once_with(local_path_to_data, "wb")

#         # Check if sys.exit was called (i.e., failure cases)
#         mock_exit.assert_not_called()


import pytest
from unittest.mock import MagicMock, mock_open, patch
from src.docker_functions import create_openvpn_config

@patch('docker.DockerClient')
def test_create_openvpn_config(mock_docker_client):
    mock_container = MagicMock()
    mock_docker_client.containers.get.return_value = mock_container
    mock_container.exec_run.return_value = (0, "Command executed")
    mock_container.get_archive.return_value = (MagicMock(), MagicMock())  # Mock get_archive
    
    user_name = "test_user"
    counter = 1
    host_address = "192.168.1.1"
    save_path = "/save/path"
    new_push_route = "192.168.1.0/24"

    with patch("ovpn_helper_functions.curl_client_ovpn_file_version") as mock_curl, \
         patch("os.makedirs") as mock_makedirs, \
         patch("builtins.open", mock_open()) as mock_open, \
         patch("sys.exit") as mock_exit:
        # Mock the directory creation to avoid permission errors
        mock_makedirs.return_value = None
        mock_open.return_value = MagicMock()
        
        create_openvpn_config(mock_docker_client, user_name, counter, host_address, save_path, new_push_route)
        
        # Ensure that the correct path is used in the call
        local_save_path = f"{save_path}/data/{user_name}"
        local_path_to_data = f"{save_path}/data/{user_name}/dockovpn_data.tar"
        mock_makedirs.assert_called_once_with(local_save_path, exist_ok=True)
        mock_open.assert_called_once_with(local_path_to_data, "wb")

        # Check if sys.exit was called (i.e., failure cases)
        mock_exit.assert_not_called()
