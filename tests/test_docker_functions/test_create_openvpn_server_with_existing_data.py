import pytest
from unittest.mock import MagicMock, patch
import docker
from src.docker_functions import create_openvpn_server_with_existing_data


# Mock everything related to docker and the create_openvpn_server_with_existing_data function
@patch("docker.DockerClient")
@patch("docker.types.EndpointConfig")
def test_create_openvpn_server_with_existing_data(
    mock_endpoint_config, mock_docker_client
):
    # Arrange
    mock_client = MagicMock()
    mock_docker_client.return_value = mock_client

    mock_container = MagicMock()
    mock_client.containers.run.return_value = mock_container

    # Mock the EndpointConfig
    mock_endpoint_config.return_value = MagicMock()

    # Define test arguments
    network_name = "test_network"
    name = "test_name"
    static_address = "192.168.1.10"
    port_number = 1194
    host_address = "10.0.0.1"
    remote_path_to_mount = "/mock/path"

    # Act
    result = create_openvpn_server_with_existing_data(
        client=mock_client,
        network_name=network_name,
        name=name,
        static_address=static_address,
        port_number=port_number,
        host_address=host_address,
        remote_path_to_mount=remote_path_to_mount,
    )

    # Assert
    assert result == mock_container  # Ensure the container object is returned

    # Check that EndpointConfig was called with the correct parameters
    mock_endpoint_config.assert_called_once_with(
        version="1.44", ipv4_address=static_address
    )

    # Ensure the Docker client's containers.run method was called with the correct arguments
    mock_client.containers.run.assert_called_once_with(
        image="alekslitvinenk/openvpn",
        detach=True,
        name=f"{name}_openvpn",
        network=network_name,
        restart_policy={"Name": "always"},
        cap_add=["NET_ADMIN"],
        ports={"1194/udp": port_number, "8080/tcp": port_number},
        environment={"HOST_ADDR": host_address},
        networking_config={network_name: mock_endpoint_config.return_value},
        volumes=[f"{remote_path_to_mount}:/opt/Dockovpn_data"],
    )


@patch("docker.DockerClient")
@patch("docker.types.EndpointConfig")
def test_create_openvpn_server_with_existing_data_api_error(
    mock_endpoint_config, mock_docker_client
):
    # Arrange
    mock_client = MagicMock()
    mock_docker_client.return_value = mock_client

    # Simulate APIError being raised
    mock_client.containers.run.side_effect = docker.errors.APIError("Mock API Error")

    # Define test arguments
    network_name = "test_network"
    name = "test_name"
    static_address = "192.168.1.10"
    port_number = 1194
    host_address = "10.0.0.1"
    remote_path_to_mount = "/mock/path"

    # Act & Assert
    with pytest.raises(docker.errors.APIError, match="Mock API Error"):
        create_openvpn_server_with_existing_data(
            client=mock_client,
            network_name=network_name,
            name=name,
            static_address=static_address,
            port_number=port_number,
            host_address=host_address,
            remote_path_to_mount=remote_path_to_mount,
        )

    # Ensure the Docker client's containers.run method was called before the exception
    mock_client.containers.run.assert_called_once()
