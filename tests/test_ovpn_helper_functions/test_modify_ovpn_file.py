import os
import shutil
import pytest

def modify_ovpn_file(file_path, new_port, new_route_ip):
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        return

    modified_lines = []

    with open(file_path, 'r') as file:
        lines = file.readlines()

    remote_line_found = False

    for line in lines:
        if line.startswith("remote "):
            parts = line.split()
            if len(parts) == 3:
                parts[-1] = str(new_port)
                line = " ".join(parts) + "\n"
                remote_line_found = True

            modified_lines.append(line)
            modified_lines.append("route-nopull\n")
            modified_lines.append(f"route {new_route_ip} 255.255.255.0\n")
        else:
            modified_lines.append(line)

    if not remote_line_found:
        print("No 'remote' line found in the file.")
        return

    with open(file_path, 'w') as file:
        file.writelines(modified_lines)

@pytest.fixture
def copy_ovpn_file():
    original_file = "client.ovpn"  # Replace with the path to your actual .ovpn file
    if not os.path.exists(original_file):
        pytest.skip("Original .ovpn file does not exist")

    # Create a copy of the original .ovpn file in the current working directory
    copied_file = os.path.join(os.getcwd(), "client_copy.ovpn")
    shutil.copyfile(original_file, copied_file)

    yield copied_file

    # Commenting out cleanup to keep the copied file
    # os.remove(copied_file)

def test_modify_ovpn_file(copy_ovpn_file):
    new_port = 443
    new_route_ip = "10.13.0.0"

    modify_ovpn_file(copy_ovpn_file, new_port, new_route_ip)

    with open(copy_ovpn_file, 'r') as file:
        lines = file.readlines()

    # Check if the remote line is updated
    remote_line_updated = False
    route_nopull_inserted = False
    route_line_inserted = False

    for i, line in enumerate(lines):
        if line.startswith("remote "):
            parts = line.split()
            assert parts[2] == str(new_port)
            remote_line_updated = True

            assert lines[i+1] == "route-nopull\n"
            assert lines[i+2] == f"route {new_route_ip} 255.255.255.0\n"
            route_nopull_inserted = True
            route_line_inserted = True
            break

    assert remote_line_updated, "Remote line was not updated"
    assert route_nopull_inserted, "route-nopull line was not inserted"
    assert route_line_inserted, "route line was not inserted"

if __name__ == "__main__":
    pytest.main()
