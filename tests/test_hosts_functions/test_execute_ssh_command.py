import pytest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from src.hosts_functions import execute_ssh_command

@patch('paramiko.SSHClient')
def test_execute_ssh_command_success(mock_ssh_client):
    mock_ssh = MagicMock()
    mock_ssh_client.return_value = mock_ssh
    
    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b"Command output"
    
    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b""
    
    mock_ssh.exec_command.return_value = (None, mock_stdout, mock_stderr)
    
    output, error = execute_ssh_command('user@192.168.1.1', 'ls')
    
    assert output == "Command output"
    assert error == ""

@patch('paramiko.SSHClient')
def test_execute_ssh_command_error(mock_ssh_client):
    mock_ssh = MagicMock()
    mock_ssh_client.return_value = mock_ssh
    
    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b""
    
    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b"Command error"
    
    mock_ssh.exec_command.return_value = (None, mock_stdout, mock_stderr)
    
    output, error = execute_ssh_command('user@192.168.1.1', 'ls')
    
    assert output == ""
    assert error == "Command error"

@patch('paramiko.SSHClient')
def test_execute_ssh_command_exception(mock_ssh_client):
    mock_ssh = MagicMock()
    mock_ssh_client.return_value = mock_ssh
    
    mock_ssh.exec_command.side_effect = Exception("SSH failed")
    
    output, error = execute_ssh_command('user@192.168.1.1', 'ls')
    
    assert output is None
    assert error == "SSH failed"
