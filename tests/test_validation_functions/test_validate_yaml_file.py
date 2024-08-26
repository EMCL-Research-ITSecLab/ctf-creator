import pytest
import os
import tempfile
import yaml
from click import BadParameter
from src.validation_functions import validate_yaml_file


def test_validate_yaml_file_valid_yaml():
    # Create a temporary YAML file in text mode
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode='w', delete=False) as tmpfile:
        yaml.dump({"key": "value"}, tmpfile)
        tmpfile_name = tmpfile.name  # Store the file name before closing

    # Now validate the YAML file
    result = validate_yaml_file(None, None, tmpfile_name)
    assert result == tmpfile_name

    # Clean up the file after the test
    os.remove(tmpfile_name)

def test_validate_yaml_file_invalid_extension():
    # Create a temporary file with an invalid extension
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmpfile:
        tmpfile.close()
        with pytest.raises(BadParameter) as excinfo:
            validate_yaml_file(None, None, tmpfile.name)
        assert "must have a .yaml or .yml extension" in str(excinfo.value)
        os.remove(tmpfile.name)

def test_validate_yaml_file_non_existent():
    # Non-existent file path
    non_existent_file = "/path/does/not/exist.yaml"
    with pytest.raises(BadParameter) as excinfo:
        validate_yaml_file(None, None, non_existent_file)
    assert "does not exist" in str(excinfo.value)

def test_validate_yaml_file_not_a_file():
    # Create a temporary directory to simulate passing a directory instead of a file
    with tempfile.TemporaryDirectory() as tmpdirname:
        with pytest.raises(BadParameter) as excinfo:
            validate_yaml_file(None, None, tmpdirname)
        assert "not a file" in str(excinfo.value)

def test_validate_yaml_file_invalid_yaml():
    # Create a temporary YAML file with invalid YAML content
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmpfile:
        tmpfile.write(b"invalid: [unclosed list")
        tmpfile.close()
        with pytest.raises(BadParameter) as excinfo:
            validate_yaml_file(None, None, tmpfile.name)
        assert "not a valid YAML file" in str(excinfo.value)
        os.remove(tmpfile.name)