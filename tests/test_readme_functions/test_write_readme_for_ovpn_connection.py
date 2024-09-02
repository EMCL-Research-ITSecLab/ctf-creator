import os
import pytest
from unittest.mock import patch, mock_open
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)
from src.readme_functions import write_readme_for_ovpn_connection

# Test parameters
test_location = "test_directory"
test_subnet = "192.168.1"
test_containers = ["container1", "container2", "container3"]


def test_write_readme_for_ovpn_connection_correct_content():
    # Expected content based on the input parameters
    expected_content = """
    # OpenVPN Connection Instructions

    To connect to the desired subnet, use the following command: "sudo openvpn client.ovpn" 

    Once connected, you can only reach the Docker containers within the subnet. The possible reachable IP addresses with `ping` are:

    - 192.168.1.1
    - 192.168.1.2
    - 192.168.1.3
    - 192.168.1.4
    - 192.168.1.5
    """.strip()

    with patch("os.makedirs") as mock_makedirs, patch(
        "builtins.open", mock_open()
    ) as mock_file:

        # Call the function
        write_readme_for_ovpn_connection(test_location, test_subnet, test_containers)

        # Assert that the directory was created
        mock_makedirs.assert_called_once_with(test_location, exist_ok=True)

        # Assert that the file was opened in write mode
        mock_file.assert_called_once_with(os.path.join(test_location, "README.md"), "w")

        # Assert that the correct content was written to the file
        mock_file().write.assert_called_once_with(expected_content)


def test_write_readme_for_ovpn_connection_no_containers():
    # Test with no containers to check the base content
    expected_content = """
    # OpenVPN Connection Instructions

    To connect to the desired subnet, use the following command: "sudo openvpn client.ovpn" 

    Once connected, you can only reach the Docker containers within the subnet. The possible reachable IP addresses with `ping` are:

    - 192.168.1.1
    - 192.168.1.2
    """.strip()

    with patch("os.makedirs") as mock_makedirs, patch(
        "builtins.open", mock_open()
    ) as mock_file:

        # Call the function
        write_readme_for_ovpn_connection(test_location, test_subnet, [])

        # Assert that the directory was created
        mock_makedirs.assert_called_once_with(test_location, exist_ok=True)

        # Assert that the file was opened in write mode
        mock_file.assert_called_once_with(os.path.join(test_location, "README.md"), "w")

        # Assert that the correct content was written to the file
        mock_file().write.assert_called_once_with(expected_content)


def test_write_readme_for_ovpn_connection_single_container():
    # Test with one container to ensure the content is correct
    expected_content = """
    # OpenVPN Connection Instructions

    To connect to the desired subnet, use the following command: "sudo openvpn client.ovpn" 

    Once connected, you can only reach the Docker containers within the subnet. The possible reachable IP addresses with `ping` are:

    - 192.168.1.1
    - 192.168.1.2
    - 192.168.1.3
    """.strip()

    with patch("os.makedirs") as mock_makedirs, patch(
        "builtins.open", mock_open()
    ) as mock_file:

        # Call the function
        write_readme_for_ovpn_connection(test_location, test_subnet, ["container1"])

        # Assert that the directory was created
        mock_makedirs.assert_called_once_with(test_location, exist_ok=True)

        # Assert that the file was opened in write mode
        mock_file.assert_called_once_with(os.path.join(test_location, "README.md"), "w")

        # Assert that the correct content was written to the file
        mock_file().write.assert_called_once_with(expected_content)
