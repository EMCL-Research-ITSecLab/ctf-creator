import pytest
from unittest.mock import patch, MagicMock, call
import docker.errors
from src.docker_functions import create_network
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Mock for the Docker client
@pytest.fixture
def mock_docker_client():
    return MagicMock()

def test_create_network(mock_docker_client):
    mock_network = MagicMock()
    mock_docker_client.networks.create.return_value = mock_network

    name = "test_network"
    subnet_ = "192.168.1.0/24"
    gateway_ = "192.168.1.1"

    # Define the expected IPAM configuration structure
    expected_ipam_config = {
        'Driver': 'default',
        'Config': [{
            'Subnet': subnet_,
            'IPRange': None,
            'Gateway': gateway_,
            'AuxiliaryAddresses': None
        }]
    }

    network = create_network(mock_docker_client, name, subnet_, gateway_)

    mock_docker_client.networks.create.assert_called_once_with(
        name,
        driver="bridge",
        ipam=expected_ipam_config,
        check_duplicate=True
    )
    assert network == mock_network
