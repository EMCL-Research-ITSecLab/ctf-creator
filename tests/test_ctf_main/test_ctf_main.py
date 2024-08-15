import pytest
import sys
import os
import yaml
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from src.ctf_main import main

#!!! Not finished add more test cases like 1-2 

@pytest.mark.parametrize("yaml_data", [
    {
        "name": "test_ctf",
        "containers": ["nginx:latest"],
        "users": ["user1", "user2"],
        "identityFile": ["/home/nick/Data/ssh_key"],
        "hosts": ["ubuntu@10.20.30.101"],
        "subnet_first_part": [10],
        "subnet_second_part": [0],
        "subnet_third_part": [1]
    }
])


@patch('src.ctf_main.yaml.safe_load')
@patch('src.ctf_main.open', create=True)
@patch('src.ctf_main.subprocess.run')
@patch('src.ctf_main.docker.DockerClient')
@patch('src.ctf_main.yaml_func.read_data_from_yaml')
@patch('src.ctf_main.hosts_func.check_host_reachability_with_ping')
@patch('src.ctf_main.hosts_func.check_host_reachability_with_SSH')
@patch('src.ctf_main.hosts_func.execute_ssh_command')
def test_main_success(mock_execute_ssh, mock_check_ssh, mock_check_ping, mock_read_yaml, mock_docker, mock_subprocess, mock_open, mock_safe_load, yaml_data):
    """
    Test the main function for a successful run.
    """
    # Setup the mocks
    mock_open.return_value.__enter__.return_value = MagicMock()
    mock_safe_load.return_value = yaml_data
    mock_read_yaml.return_value = (
        yaml_data["containers"],
        yaml_data["users"],
        yaml_data["identityFile"],
        yaml_data["hosts"],
        yaml_data["subnet_first_part"],
        yaml_data["subnet_second_part"],
        yaml_data["subnet_third_part"],
    )

    # Mock the Docker client and its methods
    mock_docker_client = MagicMock()
    mock_docker.return_value = mock_docker_client

    # Mock the methods called on the Docker client
    mock_docker_client.containers.prune.return_value = None
    mock_docker_client.networks.prune.return_value = None

    # Mock the list of containers to return a list of mock containers
    mock_container = MagicMock()
    mock_docker_client.containers.list.return_value = [mock_container]

    # Mock the stop and remove methods on the mock container
    mock_container.stop.return_value = None
    mock_container.remove.return_value = None

    # Mock the subprocess.run to simulate successful command execution
    mock_subprocess.return_value.returncode = 0  # Indicate success

    # Mock the SSH command execution
    mock_execute_ssh.return_value = None

    # CLI runner to simulate command-line input
    runner = CliRunner()
    result = runner.invoke(main, ['--config', 'fake_path.yaml', '--save_path', '/fake_save_path'])

    # Print output to understand what's happening
    print("CLI Output:", result.output)

    # Assertions
    assert result.exit_code == 0, f"Unexpected exit code: {result.exit_code}\nOutput: {result.output}"
    assert "YAML file loaded successfully." in result.output
    assert "Start to clean up the Hosts. Deletes old Docker-containers and networks" in result.output
    assert "Clean up process on hosts finished!" in result.output

    # Ensure the Docker client methods were called as expected
    assert mock_docker_client.containers.prune.called
    assert mock_docker_client.networks.prune.called
    assert mock_docker_client.containers.list.called
    assert mock_container.stop.called
    assert mock_container.remove.called

    # Ensure the SSH command was executed
    assert mock_execute_ssh.called
    assert mock_check_ssh.called
    assert mock_check_ping.called
    assert mock_check_ping.call_count == 1

@patch('src.ctf_main.yaml.safe_load')
@patch('src.ctf_main.subprocess.run', return_value=MagicMock(returncode=1))
@patch('src.ctf_main.open', create=True)
def test_main_ping_error(mock_open, mock_run, mock_safe_load):
    """
  
    """
    mock_open.return_value.__enter__.return_value = MagicMock()
    mock_safe_load.return_value = {
        "name": "test_ctf",
        "containers": ["nginx:latest"],
        "users": ["user1", "user2"],
        "identityFile": ["/home/nick/Data/ssh_key"],
        "hosts": ["ubuntu@4.5.4.3"],
        "subnet_first_part": [10],
        "subnet_second_part": [0],
        "subnet_third_part": [1]
    }

    runner = CliRunner()
    result = runner.invoke(main, ['--config', 'fake_path.yaml', '--save_path', '/fake_save_path'])

    assert result.exit_code == 1  
    assert "The following hosts are unreachable" in result.output
    print(result.output)
    assert "Please check if you are connected to the correct WireGuard VPN" in result.output





