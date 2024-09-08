import pytest
from unittest.mock import patch, MagicMock
from src.docker_functions import create_openvpn_server


@patch("docker.DockerClient")
def test_create_openvpn_server(mock_docker_client):
    mock_container = MagicMock()
    mock_docker_client.containers.run.return_value = mock_container

    network_name = "test_network"
    name = "test_openvpn"
    static_address = "192.168.1.3"
    counter = 1
    host_address = "192.168.1.1"

    container = create_openvpn_server(
        mock_docker_client, network_name, name, static_address, counter, host_address
    )

    expected_networking_config = {
        network_name: {"IPAMConfig": {"IPv4Address": static_address}}
    }

    mock_docker_client.containers.run.assert_called_once_with(
        image="alekslitvinenk/openvpn",
        detach=True,
        name=f"{name}_openvpn",
        network=network_name,
        restart_policy={"Name": "always"},
        cap_add=["NET_ADMIN"],
        ports={"1194/udp": 1195, "8080/tcp": 81},
        environment={"HOST_ADDR": host_address},
        networking_config=expected_networking_config,
    )
