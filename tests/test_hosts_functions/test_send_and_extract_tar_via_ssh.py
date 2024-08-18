import pytest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from src.hosts_functions import send_and_extract_tar_via_ssh

@patch('paramiko.SSHClient')
@patch('os.path.dirname')
def test_send_and_extract_tar_via_ssh_success(mock_dirname, mock_ssh_client):
    mock_dirname.return_value = '/remote/dir'
    mock_ssh = MagicMock()
    mock_ssh_client.return_value = mock_ssh
    
    # Mock exec_command for mkdir and tar extraction
    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b""
    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b""
    
    mock_ssh.exec_command.return_value = (None, mock_stdout, mock_stderr)
    
    # Mock SFTP put
    mock_sftp = MagicMock()
    mock_ssh.open_sftp.return_value = mock_sftp
    
    send_and_extract_tar_via_ssh('/local/path.tar', 'user', '192.168.1.1', '/remote/path.tar')
    
    mock_ssh.exec_command.assert_any_call('mkdir -p /remote/dir')
    mock_sftp.put.assert_called_once_with('/local/path.tar', '/remote/path.tar')
    mock_ssh.exec_command.assert_any_call('tar -xf /remote/path.tar -C /remote/dir')

@patch('paramiko.SSHClient')
@patch('os.path.dirname')
def test_send_and_extract_tar_via_ssh_mkdir_failure(mock_dirname, mock_ssh_client):
    mock_dirname.return_value = '/remote/dir'
    mock_ssh = MagicMock()
    mock_ssh_client.return_value = mock_ssh
    
    # Mock exec_command for mkdir to simulate error
    mock_stdout = MagicMock()
    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b"mkdir: cannot create directory"
    
    mock_ssh.exec_command.return_value = (None, mock_stdout, mock_stderr)
    
    send_and_extract_tar_via_ssh('/local/path.tar', 'user', '192.168.1.1', '/remote/path.tar')
    
    mock_ssh.exec_command.assert_any_call('mkdir -p /remote/dir')
    mock_ssh.open_sftp.assert_not_called()  # Should not proceed to SFTP

@patch('paramiko.SSHClient')
@patch('os.path.dirname')
def test_send_and_extract_tar_via_ssh_exception(mock_dirname, mock_ssh_client):
    mock_dirname.return_value = '/remote/dir'
    mock_ssh = MagicMock()
    mock_ssh_client.return_value = mock_ssh
    
    # Simulate SSH connection error
    mock_ssh.connect.side_effect = Exception("Connection failed")
    
    send_and_extract_tar_via_ssh('/local/path.tar', 'user', '192.168.1.1', '/remote/path.tar')
    
    mock_ssh.connect.assert_called_once()
    mock_ssh.exec_command.assert_not_called()  # Should not proceed if connection fails
