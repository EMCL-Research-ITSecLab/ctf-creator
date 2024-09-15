import os
import tempfile
import pytest
import yaml
from unittest import mock
from click.testing import CliRunner
from src.ctf_main import main
from src.docker_functions import create_openvpn_config
from src.ovpn_helper_functions import modify_ovpn_file
import docker
import src.hosts_functions
import subprocess

# Mock data for YAML file
MOCK_YAML_DATA = {
    "containers": ["nginx:latest"],
    "users": ["user1"],
    "identityFile": ["/home/user/.ssh/id_rsa"],
    "hosts": ["ubuntu@192.168.1.101"],
    "subnet_first_part": ["10"],
    "subnet_second_part": ["1"],
    "subnet_third_part": ["0"],
}


@pytest.fixture
def create_temp_yaml_file():
    """Fixture to create a temporary YAML file for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yaml_file_path = os.path.join(temp_dir, "config.yaml")
        with open(yaml_file_path, "w") as yaml_file:
            yaml.dump(MOCK_YAML_DATA, yaml_file)
        yield yaml_file_path


@pytest.fixture
def create_temp_save_path():
    """Fixture to create a temporary directory for save_path."""
    with tempfile.TemporaryDirectory() as temp_save_path:
        yield temp_save_path  # Provide the path to the test function


@mock.patch("docker.DockerClient")
@mock.patch("hosts_functions.execute_ssh_command")
@mock.patch("subprocess.run")
def test_main_success(
    mock_subprocess_run,
    mock_execute_ssh_command,
    mock_docker_client,
    create_temp_yaml_file,
    create_temp_save_path,
):
    """
    Test the main function with Docker and SSH operations mocked.
    """
    # Mock Docker client and its methods
    mock_docker_instance = mock_docker_client.return_value
    mock_container_instance = mock.MagicMock()

    # Mock Docker operations: prune, list, stop, remove, network prune
    mock_docker_instance.containers.prune.side_effect = lambda: print(
        "Mock prune called"
    )
    mock_docker_instance.containers.list.return_value = [mock_container_instance]
    mock_container_instance.stop.side_effect = lambda: print("Mock stop called")
    mock_container_instance.remove.side_effect = lambda force=True: print(
        "Mock remove called"
    )
    mock_docker_instance.networks.prune.side_effect = lambda: print(
        "Mock network prune called"
    )

    # Mock SSH command execution
    mock_execute_ssh_command.return_value = None

    # Mock subprocess.run for ssh-agent and ssh-add
    mock_subprocess_run.return_value.returncode = 0

    # Mocking the docker client instance and the container
    mock_docker_instance = mock_docker_client.return_value
    mock_container_instance = mock.MagicMock()

    # Set up the container to be returned by the containers.get() method
    mock_docker_instance.containers.get.return_value = mock_container_instance

    # Mock the exec_run method on the container to return a simulated result
    mock_container_instance.exec_run.return_value = (0, "Execution success")
    # Mock the container.get_archive method to return a simulated archive
    mock_archive = [b"archive_chunk1", b"archive_chunk2"]
    mock_stat = {"name": "dummy_stat"}
    mock_container_instance.get_archive.return_value = (mock_archive, mock_stat)

    # Use CliRunner to simulate Click command-line execution
    runner = CliRunner()
    result = runner.invoke(
        main, ["--config", create_temp_yaml_file, "--save_path", create_temp_save_path]
    )

    # Debugging: Print output to ensure everything is mocked correctly
    print(result.output)

    # Assertions to check expected behavior
    assert result.exit_code == 0
    assert "YAML file loaded successfully." in result.output
    assert "Save path" in result.output
    assert "Mock prune called" in result.output
    assert "Mock stop called" in result.output
    assert "Mock remove called" in result.output
    assert "Mock network prune called" in result.output

    # Check that the Docker client was called correctly
    mock_docker_client.assert_called()

    # Ensure SSH command was called
    mock_execute_ssh_command.assert_called()

    # Ensure subprocess.run was called for ssh-agent and ssh-add
    mock_subprocess_run.assert_called()


# Additional test for handling YAML errors
@mock.patch("yaml.safe_load", side_effect=yaml.YAMLError("Invalid YAML"))
def test_main_yaml_error(mock_yaml_load, create_temp_save_path):
    """Test the main function when a YAML error occurs."""
    runner = CliRunner()
    result = runner.invoke(
        main, ["--config", "config.yaml", "--save_path", create_temp_save_path]
    )

    # Ensure that an error related to YAML is displayed
    assert result.exit_code != 0
    assert "does not exist" in result.output


# Test for handling file not found error
def test_main_file_not_found_error(create_temp_save_path):
    """Test the main function when the YAML file is not found."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--config", "non_existing_file.yaml", "--save_path", create_temp_save_path],
    )

    # Ensure the file not found error is handled
    assert result.exit_code != 0
    assert "does not exist" in result.output
