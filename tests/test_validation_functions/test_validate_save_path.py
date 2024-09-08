from src.validation_functions import validate_save_path
from click import BadParameter
import pytest
import os
import tempfile
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)


def test_validate_save_path_valid_directory():
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdirname:
        result = validate_save_path(None, None, tmpdirname)
        assert result == tmpdirname


def test_validate_save_path_non_existent_directory():
    # Create a temporary directory and a non-existent subdirectory
    with tempfile.TemporaryDirectory() as tmpdirname:
        non_existent_path = os.path.join(tmpdirname, "non_existent")
        result = validate_save_path(None, None, non_existent_path)
        assert result == non_existent_path
        assert os.path.isdir(non_existent_path)


def test_validate_save_path_not_a_directory():
    # Create a temporary file to simulate an invalid directory path
    with tempfile.NamedTemporaryFile() as tmpfile:
        with pytest.raises(BadParameter) as excinfo:
            validate_save_path(None, None, tmpfile.name)
        assert "not a directory" in str(excinfo.value)


def test_validate_save_path_invalid_directory():
    # Invalid directory path (e.g., reserved characters in path)
    with pytest.raises(BadParameter) as excinfo:
        validate_save_path(None, None, "/invalid\0path")
    assert "invalid" in str(excinfo.value)
