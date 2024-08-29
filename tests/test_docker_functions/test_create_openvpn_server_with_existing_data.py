import pytest
from unittest.mock import patch, MagicMock, call
import docker.errors
from src.docker_functions import create_openvpn_server_with_existing_data
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# # Mock for the Docker client
# @pytest.fixture
# def mock_docker_client():
#     return MagicMock()

# def test_create_openvpn_server_with_existing_data(mock_docker_client):
#     mock_container = MagicMock()
#     mock_docker_client.containers.run.return_value = mock_container

#     network_name = "test_network"
#     name = "test_openvpn"
#     static_address = "192.168.1.3"
#     counter = 1
#     host_address = "192.168.1.1"
#     remote_path_to_mount = "/path/on/host"

#     container = create_openvpn_server_with_existing_data(
#         mock_docker_client, network_name, name, static_address, counter, host_address, remote_path_to_mount
#     )

#     mock_docker_client.containers.run.assert_called_once_with(
#         image="alekslitvinenk/openvpn",
#         detach=True,
#         name=f"{name}_openvpn",
#         network=network_name,
#         restart_policy={"Name": "always"},
#         cap_add=["NET_ADMIN"],
#         ports={
#             '1194/udp': 1195,
#             '8080/tcp': 81
#         },
#         environment={
#             "HOST_ADDR": f"{host_address}",
#         },
#         networking_config={network_name: mock_container.endpoint_config.return_value},
#         volumes=[f"{remote_path_to_mount}:/opt/Dockovpn_data"]
#     )
#     assert container == mock_container

import pytest
from unittest.mock import MagicMock, patch
from docker_functions import create_openvpn_server_with_existing_data

@patch('docker.DockerClient')
def test_create_openvpn_server_with_existing_data(mock_docker_client):
    mock_container = MagicMock()
    mock_docker_client.containers.run.return_value = mock_container
    
    network_name = "test_network"
    name = "test_openvpn"
    static_address = "192.168.1.3"
    counter = 1
    host_address = "192.168.1.1"
    remote_path_to_mount = "/path/on/host"
    
    container = create_openvpn_server_with_existing_data(
        mock_docker_client, network_name, name, static_address, counter, host_address, remote_path_to_mount
    )
    
    expected_networking_config = {network_name: {'IPAMConfig': {'IPv4Address': static_address}}}
    
    mock_docker_client.containers.run.assert_called_once_with(
        image="alekslitvinenk/openvpn",
        detach=True,
        name=f"{name}_openvpn",
        network=network_name,
        restart_policy={"Name": "always"},
        cap_add=["NET_ADMIN"],
        ports={'1194/udp': 1195, '8080/tcp': 81},
        environment={"HOST_ADDR": host_address},
        networking_config=expected_networking_config,
        volumes=[f"{remote_path_to_mount}:/opt/Dockovpn_data"]
    )
