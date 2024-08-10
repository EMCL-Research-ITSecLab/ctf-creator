# import pytest
# from unittest.mock import MagicMock, patch
# from io import StringIO
# import tarfile
# from src.tar_functions import untar_data

#!!! DIESER TEST funktionitert noch nicht

import os
import pytest
from unittest.mock import patch
from src.tar_functions import untar_data
import tarfile



@pytest.fixture
def temp_dir(tmpdir):
    """Creates a temporary directory for testing."""
    yield tmpdir.strpath


@pytest.mark.parametrize(
    "tar_file_path, destination_dir, expected_output",
    [
        ("valid.tar", "dest_dir", "Data extracted from valid.tar to dest_dir"),
        ("invalid.tar", "dest_dir", "Error reading tar file: .*"),  # .* matches any characters
        ("valid.tar", "nonexistent_dir", "Error: File 'nonexistent_dir' not found."),
    ],
)
def test_untar_data(temp_dir, tar_file_path, destination_dir, expected_output):
    # Create a temporary tar file (optional, replace with your own logic)
    with open(os.path.join(temp_dir, "data.txt"), "w") as f:
        f.write("This is some test data")
    with tarfile.open(os.path.join(temp_dir, "valid.tar"), "w:gz") as tar:
        tar.add(os.path.join(temp_dir, "data.txt"))

    # Mock the print function to capture output
    with patch("your_file.print") as mock_print:
        untar_data(os.path.join(temp_dir, tar_file_path), os.path.join(temp_dir, destination_dir))

    # Assert expected output
    mock_print.assert_called_once_with(expected_output)


# @patch('tarfile.open')
# def test_untar_data_success(mock_tarfile):
#     # Arrange
#     tar_file_path = 'test.tar'
#     destination_dir = 'test_dir'
    
#     # Create a mock tarfile object
#     mock_tar = MagicMock()
#     mock_tarfile.return_value = mock_tar
    
#     # Act
#     with patch('sys.stdout', new=StringIO()) as fake_out:
#         untar_data(tar_file_path, destination_dir)
        
#         # Assert
#         mock_tarfile.assert_called_once_with(tar_file_path, 'r')
#         mock_tar.extractall.assert_called_once_with(destination_dir)
#         assert "Data extracted from test.tar to test_dir" in fake_out.getvalue()

# @patch('tarfile.open')
# def test_untar_data_file_not_found(mock_tarfile):
#     # Arrange
#     tar_file_path = 'non_existent.tar'
#     destination_dir = 'test_dir'
    
#     # Simulate FileNotFoundError
#     mock_tarfile.side_effect = FileNotFoundError
    
#     # Act
#     with patch('sys.stdout', new=StringIO()) as fake_out:
#         untar_data(tar_file_path, destination_dir)
        
#         # Assert
#         assert "Error: File 'non_existent.tar' not found." in fake_out.getvalue()

# @patch('tarfile.open')
# def test_untar_data_read_error(mock_tarfile):
#     # Arrange
#     tar_file_path = 'corrupt.tar'
#     destination_dir = 'test_dir'
    
#     # Simulate tarfile.ReadError
#     mock_tarfile.side_effect = tarfile.ReadError("ReadError")
    
#     # Act
#     with patch('sys.stdout', new=StringIO()) as fake_out:
#         untar_data(tar_file_path, destination_dir)
        
#         # Assert
#         assert "Error reading tar file: ReadError" in fake_out.getvalue()

# @patch('tarfile.open')
# def test_untar_data_tar_error(mock_tarfile):
#     # Arrange
#     tar_file_path = 'invalid.tar'
#     destination_dir = 'test_dir'
    
#     # Simulate tarfile.TarError
#     mock_tarfile.side_effect = tarfile.TarError("TarError")
    
#     # Act
#     with patch('sys.stdout', new=StringIO()) as fake_out:
#         untar_data(tar_file_path, destination_dir)
        
#         # Assert
#         assert "Error extracting tar archive: TarError" in fake_out.getvalue()
