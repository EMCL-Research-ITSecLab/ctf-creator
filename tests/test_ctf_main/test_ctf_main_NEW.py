# import pytest
# import sys
# import os
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
# from unittest.mock import patch, MagicMock
# from click.testing import CliRunner
# from src.ctf_main import main
# import yaml
# # Mock function and object paths should be updated according to your module structure.

# @pytest.mark.parametrize("yaml_data", [
#     {
#         "name": "test_ctf",
#         "containers": ["nginx:latest"],
#         "users": ["user1", "user2"],
#         "identityFile": ["/home/nick/Data/ssh_key"],
#         "hosts": ["ubuntu@10.20.30.101"],
#         "subnet_first_part": [10],
#         "subnet_second_part": [0],
#         "subnet_third_part": [1]
#     }
# ])
# @patch('src.ctf_main.yaml.safe_load')
# @patch('src.ctf_main.open', create=True)
# @patch('src.ctf_main.subprocess.run')
# @patch('src.ctf_main.docker.DockerClient')
# @patch('src.ctf_main.yaml_func.read_data_from_yaml')
# @patch('src.ctf_main.hosts_func.check_host_reachability_with_ping')
# @patch('src.ctf_main.hosts_func.check_host_reachability_with_SSH')
# def test_main_success(mock_check_ssh, mock_check_ping, mock_read_yaml, mock_docker, mock_subprocess, mock_open, mock_safe_load, yaml_data):
#     """
#     Test the main function for a successful run.
#     """
#     # Setup the mocks
#     mock_open.return_value.__enter__.return_value = MagicMock()
#     mock_safe_load.return_value = yaml_data
#     mock_read_yaml.return_value = (
#         yaml_data["containers"],
#         yaml_data["users"],
#         yaml_data["identityFile"],
#         yaml_data["hosts"],
#         yaml_data["subnet_first_part"],
#         yaml_data["subnet_second_part"],
#         yaml_data["subnet_third_part"],
#     )
    
#     # Mock subprocess to succeed
#     mock_subprocess.return_value = MagicMock(returncode=0)
#     mock_docker.return_value = MagicMock()

#     runner = CliRunner()
#     result = runner.invoke(main, ['--config', 'fake_path.yaml', '--save_path', '/fake_save_path'])

#     # Assertions
#     assert result.exit_code == 0
#     assert "YAML file loaded successfully." in result.output
#     assert mock_check_ssh.called
#     assert mock_check_ping.called

# @pytest.mark.parametrize("yaml_data", [
#     {
#         "name": "test_ctf",
#         "containers": ["nginx:latest"],
#         "users": ["user1", "user2"],
#         "identityFile": ["/home/nick/Data/ssh_key"],
#         "hosts": ["ubuntu@4.5.4.3"],
#         "subnet_first_part": [10],
#         "subnet_second_part": [0],
#         "subnet_third_part": [1]
#     }
# ])
# @patch('src.ctf_main.yaml.safe_load')
# @patch('src.ctf_main.subprocess.run', side_effect=Exception("SSH-agent error"))
# @patch('src.ctf_main.open', create=True)
# def test_main_ssh_agent_error(mock_open, mock_run, mock_safe_load, yaml_data):
#     """
#     Test the handling of SSH-agent setup failure.
#     """
#     mock_open.return_value.__enter__.return_value = MagicMock()
#     mock_safe_load.return_value = yaml_data

#     runner = CliRunner()
#     result = runner.invoke(main, ['--config', 'fake_path.yaml', '--save_path', '/fake_save_path'])

#     assert result.exit_code == 1
#     assert "Error executing command: eval \"$(ssh-agent)\"" in result.output

# @pytest.mark.parametrize("yaml_data", [
#     {
#         "name": "test_ctf",
#         "containers": ["nginx:latest"],
#         "users": ["user1", "user2"],
#         "identityFile": ["/home/nick/Data/ssh_key"],
#         "hosts": ["ubuntu@4.5.4.3"],
#         "subnet_first_part": [10],
#         "subnet_second_part": [0],
#         "subnet_third_part": [1]
#     }
# ])
# @patch('src.ctf_main.yaml.safe_load')
# @patch('src.ctf_main.subprocess.run', return_value=MagicMock(returncode=0))
# @patch('src.ctf_main.hosts_func.check_host_reachability_with_SSH', side_effect=Exception("SSH check failed"))
# @patch('src.ctf_main.open', create=True)
# def test_main_ssh_check_error(mock_open, mock_check_ssh, mock_subprocess, mock_safe_load, yaml_data):
#     """
#     Test handling of SSH check failure.
#     """
#     mock_open.return_value.__enter__.return_value = MagicMock()
#     mock_safe_load.return_value = yaml_data

#     runner = CliRunner()
#     result = runner.invoke(main, ['--config', 'fake_path.yaml', '--save_path', '/fake_save_path'])

#     assert result.exit_code == 1
#     assert "An unexpected error occurred: SSH check failed" in result.output

# @pytest.mark.parametrize("yaml_data", [
#     {
#         "name": "test_ctf",
#         "containers": ["nginx:latest"],
#         "users": ["user1", "user2"],
#         "identityFile": ["/home/nick/Data/ssh_key"],
#         "hosts": ["ubuntu@4.5.4.3"],
#         "subnet_first_part": [10],
#         "subnet_second_part": [0],
#         "subnet_third_part": [1]
#     }
# ])
# @patch('src.ctf_main.yaml.safe_load')
# @patch('src.ctf_main.subprocess.run', return_value=MagicMock(returncode=1))
# @patch('src.ctf_main.open', create=True)
# def test_main_ping_error(mock_open, mock_run, mock_safe_load, yaml_data):
#     """
#     Test handling of ping check failure.
#     """
#     mock_open.return_value.__enter__.return_value = MagicMock()
#     mock_safe_load.return_value = yaml_data

#     runner = CliRunner()
#     result = runner.invoke(main, ['--config', 'fake_path.yaml', '--save_path', '/fake_save_path'])

#     assert result.exit_code == 1
#     assert "The following hosts are unreachable" in result.output
#     assert "Please check if you are connected to the correct WireGuard VPN" in result.output

# @pytest.mark.parametrize("yaml_data", [
#     {
#         "name": "test_ctf",
#         "containers": ["nginx:latest"],
#         "users": ["user1", "user2"],
#         "identityFile": ["/home/nick/Data/ssh_key"],
#         "hosts": ["ubuntu@4.5.4.3"],
#         "subnet_first_part": [10],
#         "subnet_second_part": [0],
#         "subnet_third_part": [1]
#     }
# ])
# @patch('src.ctf_main.yaml.safe_load')
# @patch('src.ctf_main.open', create=True)
# def test_main_file_not_found(mock_open, mock_safe_load, yaml_data):
#     """
#     Test handling of file not found error.
#     """
#     mock_safe_load.side_effect = FileNotFoundError("File not found")

#     runner = CliRunner()
#     result = runner.invoke(main, ['--config', 'fake_path.yaml', '--save_path', '/fake_save_path'])

#     assert result.exit_code == 1
#     assert "Error: The specified file was not found." in result.output

# @pytest.mark.parametrize("yaml_data", [
#     {
#         "name": "test_ctf",
#         "containers": ["nginx:latest"],
#         "users": ["user1", "user2"],
#         "identityFile": ["/home/nick/Data/ssh_key"],
#         "hosts": ["ubuntu@4.5.4.3"],
#         "subnet_first_part": [10],
#         "subnet_second_part": [0],
#         "subnet_third_part": [1]
#     }
# ])
# @patch('src.ctf_main.yaml.safe_load', side_effect=yaml.YAMLError("YAML error"))
# @patch('src.ctf_main.open', create=True)
# def test_main_yaml_parsing_error(mock_open, mock_safe_load, yaml_data):
#     """
#     Test handling of YAML parsing error.
#     """
#     runner = CliRunner()
#     result = runner.invoke(main, ['--config', 'fake_path.yaml', '--save_path', '/fake_save_path'])

#     assert result.exit_code == 1
#     assert "Error parsing YAML file: YAML error" in result.output

# @pytest.mark.parametrize("yaml_data", [
#     {
#         "name": "test_ctf",
#         "containers": ["nginx:latest"],
#         "users": ["user1", "user2"],
#         "identityFile": ["/home/nick/Data/ssh_key"],
#         "hosts": ["ubuntu@4.5.4.3"],
#         "subnet_first_part": [10],
#         "subnet_second_part": [0],
#         "subnet_third_part": [1]
#     }
# ])
# @patch('src.ctf_main.yaml.safe_load')
# @patch('src.ctf_main.subprocess.run', side_effect=Exception("Unexpected error"))
# @patch('src.ctf_main.open', create=True)
# def test_main_unexpected_error(mock_open, mock_run, mock_safe_load, yaml_data):
#     """
#     Test handling of an unexpected error.
#     """
#     mock_open.return_value.__enter__.return_value = MagicMock()
#     mock_safe_load.return_value = yaml_data

#     runner = CliRunner()
#     result = runner.invoke(main, ['--config', 'fake_path.yaml', '--save_path', '/fake_save_path'])

#     assert result.exit_code == 1
#     assert "An unexpected error occurred: Unexpected error" in result.output
