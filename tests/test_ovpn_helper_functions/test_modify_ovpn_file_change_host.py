import pytest
import subprocess
import os
from unittest.mock import patch, mock_open, MagicMock
import time
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from src.ovpn_helper_functions import curl_client_ovpn_file_version, modify_ovpn_file, modify_ovpn_file_change_host

# def test_modify_ovpn_file_change_host_existing_remote_line():
#     file_content = """remote oldhost 1194\nclient\ndev tun\n"""
#     expected_content = """remote 192.168.0.10 1195\nclient\ndev tun\n"""

#     with patch('builtins.open', mock_open(read_data=file_content)) as mock_file, \
#          patch('os.path.exists', return_value=True):
        
#         modify_ovpn_file_change_host("dummy.ovpn", new_ip="192.168.0.10", new_port=1195)
        
#         handle = mock_file()
#         handle.write.assert_any_call(expected_content)

# def test_modify_ovpn_file_change_host_existing_remote_line():
#     file_content = """remote oldhost 1194\nclient\ndev tun\n"""
#     expected_content = """remote 192.168.0.10 1195\nclient\ndev tun\n"""

#     with patch('builtins.open', mock_open(read_data=file_content)) as mock_file, \
#          patch('os.path.exists', return_value=True):
        
#         modify_ovpn_file_change_host("dummy.ovpn", new_ip="192.168.0.10", new_port=1195)
        
#         handle = mock_file()
#         written_content = ''.join(call[0][0] for call in handle.write.call_args_list)
#         print("Written Content:\n", written_content)
        
#         assert expected_content in written_content, "Expected content not found in the written content"

import pytest
from unittest.mock import mock_open, patch
from src.ovpn_helper_functions import modify_ovpn_file_change_host

@patch('builtins.open', new_callable=mock_open, read_data="remote oldhost 1194\nclient\ndev tun\n")
@patch('os.path.exists', return_value=True)
def test_modify_ovpn_file_change_host_existing_remote_line(mock_exists, mock_file):
    expected_content = """remote 192.168.0.10 1195\nclient\ndev tun\n"""
    
    modify_ovpn_file_change_host("dummy.ovpn", new_ip="192.168.0.10", new_port=1195)
    
    handle = mock_file()
    written_content = ''.join(call[0][0] for call in handle.write.call_args_list)
    assert expected_content in written_content, "Expected content not found in the written content"


def test_modify_ovpn_file_change_host_no_remote_line():
    file_content = """client\ndev tun\n"""
    
    with patch('builtins.open', mock_open(read_data=file_content)) as mock_file, \
         patch('os.path.exists', return_value=True), \
         patch('builtins.print') as mock_print:

        modify_ovpn_file_change_host("dummy.ovpn", new_ip="192.168.0.10", new_port=1195)
        
        mock_print.assert_called_once_with("No 'remote' line found in the file.")
        mock_file().write.assert_not_called()
