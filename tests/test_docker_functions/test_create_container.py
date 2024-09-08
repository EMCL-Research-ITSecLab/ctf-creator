import pytest
from unittest.mock import MagicMock
from src.docker_functions import create_container
import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)


@pytest.fixture
def mock_docker_client():
    return MagicMock()


def test_create_container(mock_docker_client):
    # Create a mock container object
    mock_container = MagicMock()
    mock_docker_client.containers.run.return_value = mock_container

    network_name = "test_network"
    name = "test_container"
    image = "test_image"
    static_address = "192.168.1.2"

    # Define expected networking config directly
    expected_networking_config = {
        network_name: {"IPAMConfig": {"IPv4Address": static_address}}
    }

    # Run the function to test
    container = create_container(
        mock_docker_client, network_name, name, image, static_address
    )

    # Assert that the container was created with the correct parameters
    mock_docker_client.containers.run.assert_called_once_with(
        image,
        detach=True,
        name=name,
        network=network_name,
        networking_config=expected_networking_config,
    )
