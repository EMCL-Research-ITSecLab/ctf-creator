# import os
# import shutil
# import pytest

# def modify_ovpn_file(file_path, new_port, new_route_ip):
#     if not os.path.exists(file_path):
#         print(f"File {file_path} does not exist.")
#         return

#     modified_lines = []

#     with open(file_path, 'r') as file:
#         lines = file.readlines()

#     remote_line_found = False

#     for line in lines:
#         if line.startswith("remote "):
#             parts = line.split()
#             if len(parts) == 3:
#                 parts[-1] = str(new_port)
#                 line = " ".join(parts) + "\n"
#                 remote_line_found = True

#             modified_lines.append(line)
#             modified_lines.append("route-nopull\n")
#             modified_lines.append(f"route {new_route_ip} 255.255.255.0\n")
#         else:
#             modified_lines.append(line)

#     if not remote_line_found:
#         print("No 'remote' line found in the file.")
#         return

#     with open(file_path, 'w') as file:
#         file.writelines(modified_lines)

# @pytest.fixture
# def copy_ovpn_file():
#     original_file = "client.ovpn"  # Replace with the path to your actual .ovpn file
#     if not os.path.exists(original_file):
#         pytest.skip("Original .ovpn file does not exist")

#     # Create a copy of the original .ovpn file in the current working directory
#     copied_file = os.path.join(os.getcwd(), "client_copy.ovpn")
#     shutil.copyfile(original_file, copied_file)

#     yield copied_file

#     # Commenting out cleanup to keep the copied file
#     # os.remove(copied_file)

# def test_modify_ovpn_file(copy_ovpn_file):
#     new_port = 443
#     new_route_ip = "10.13.0.0"

#     modify_ovpn_file(copy_ovpn_file, new_port, new_route_ip)

#     with open(copy_ovpn_file, 'r') as file:
#         lines = file.readlines()

#     # Check if the remote line is updated
#     remote_line_updated = False
#     route_nopull_inserted = False
#     route_line_inserted = False

#     for i, line in enumerate(lines):
#         if line.startswith("remote "):
#             parts = line.split()
#             assert parts[2] == str(new_port)
#             remote_line_updated = True

#             assert lines[i+1] == "route-nopull\n"
#             assert lines[i+2] == f"route {new_route_ip} 255.255.255.0\n"
#             route_nopull_inserted = True
#             route_line_inserted = True
#             break

#     assert remote_line_updated, "Remote line was not updated"
#     assert route_nopull_inserted, "route-nopull line was not inserted"
#     assert route_line_inserted, "route line was not inserted"

# if __name__ == "__main__":
#     pytest.main()

import pytest
import subprocess
import os
from unittest.mock import patch, mock_open, MagicMock
import time
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from src.ovpn_helper_functions import curl_client_ovpn_file_version, modify_ovpn_file, modify_ovpn_file_change_host

# def test_modify_ovpn_file_existing_remote_line():
#     file_content = """remote oldhost 1194\nclient\ndev tun\n"""
#     expected_content = """remote oldhost 1195\nroute-nopull\nroute 10.8.0.1\npull-filter ignore "redirect-gateway"\npull-filter ignore "dhcp-option"\npull-filter ignore "route"\nclient\ndev tun\n"""

#     with patch('builtins.open', mock_open(read_data=file_content)) as mock_file, \
#          patch('os.path.exists', return_value=True):

#         modify_ovpn_file("dummy.ovpn", new_port=1195, new_route_ip="10.8.0.1")
        
#         mock_file().write.assert_called_once_with(expected_content)
# def test_modify_ovpn_file_existing_remote_line():
#     file_content = """remote oldhost 1194\nclient\ndev tun\n"""
#     expected_content = """remote oldhost 1195\nroute-nopull\nroute 10.8.0.1\npull-filter ignore "redirect-gateway"\npull-filter ignore "dhcp-option"\npull-filter ignore "route"\nclient\ndev tun\n"""

#     with patch('builtins.open', mock_open(read_data=file_content)) as mock_file, \
#          patch('os.path.exists', return_value=True):
        
#         modify_ovpn_file("dummy.ovpn", new_port=1195, new_route_ip="10.8.0.1")
        
#         handle = mock_file()
#         handle.write.assert_any_call(expected_content)
# def test_modify_ovpn_file_existing_remote_line():
#     file_content = """remote oldhost 1194\nclient\ndev tun\n"""
#     expected_content = """remote oldhost 1195\nroute-nopull\nroute 10.8.0.1\npull-filter ignore "redirect-gateway"\npull-filter ignore "dhcp-option"\npull-filter ignore "route"\nclient\ndev tun\n"""

#     with patch('builtins.open', mock_open(read_data=file_content)) as mock_file, \
#          patch('os.path.exists', return_value=True):
        
#         modify_ovpn_file("dummy.ovpn", new_port=1195, new_route_ip="10.8.0.1")
        
#         handle = mock_file()
#         written_content = ''.join(call[0][0] for call in handle.write.call_args_list)
#         print("Written Content:\n", written_content)
        
#         assert expected_content in written_content, "Expected content not found in the written content"

from unittest.mock import patch, mock_open

import pytest
from unittest.mock import mock_open, patch
from src.ovpn_helper_functions import modify_ovpn_file

@patch('builtins.open', new_callable=mock_open, read_data="remote oldhost 1194\nclient\ndev tun\n")
@patch('os.path.exists', return_value=True)
def test_modify_ovpn_file_existing_remote_line(mock_exists, mock_file):
    expected_content = """remote oldhost 1195\nroute-nopull\nroute 10.8.0.1\npull-filter ignore "redirect-gateway"\npull-filter ignore "dhcp-option"\npull-filter ignore "route"\nclient\ndev tun\n"""
    
    modify_ovpn_file("dummy.ovpn", new_port=1195, new_route_ip="10.8.0.1")
    
    handle = mock_file()
    written_content = ''.join(call[0][0] for call in handle.write.call_args_list)
    assert written_content == expected_content, "Expected content not found in the written content"


# def test_modify_ovpn_file_existing_remote_line():
#     file_content = """remote oldhost 1194\nclient\ndev tun\n"""
#     expected_content = """remote oldhost 1195\nroute-nopull\nroute 10.8.0.1\npull-filter ignore "redirect-gateway"\npull-filter ignore "dhcp-option"\npull-filter ignore "route"\nclient\ndev tun\n"""

#     with patch('builtins.open', mock_open(read_data=file_content)) as mock_file, \
#          patch('os.path.exists', return_value=True):

#         modify_ovpn_file("dummy.ovpn", new_port=1195, new_route_ip="10.8.0.1")

#         # Retrieve the file handle to examine what was written
#         handle = mock_file()
#         written_content = ''.join(call[0][0] for call in handle.write.call_args_list)
#         print("Written Content:\n", written_content)

#         # Compare each line separately
#         written_lines = written_content.splitlines(keepends=True)
#         expected_lines = expected_content.splitlines(keepends=True)
        
#         assert written_lines == expected_lines, "Expected content not found in the written content"

def test_modify_ovpn_file_no_remote_line():
    file_content = """client\ndev tun\n"""
    
    with patch('builtins.open', mock_open(read_data=file_content)) as mock_file, \
         patch('os.path.exists', return_value=True), \
         patch('builtins.print') as mock_print:

        modify_ovpn_file("dummy.ovpn", new_port=1195, new_route_ip="10.8.0.1")
        
        mock_print.assert_called_once_with("No 'remote' line found in the file.")
        mock_file().write.assert_not_called()