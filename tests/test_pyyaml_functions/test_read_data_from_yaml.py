import pytest
from src.pyyaml_functions import read_data_from_yaml


def test_valid_data():
    data = {
        "containers": ["nginx", "redis"],
        "users": ["user1", "user2"],
        "identityFile": ["/path/to/key"],
        "hosts": ["admin@10.0.0.0", "ubuntu@10.20.30.101"],
        "subnet_first_part": [192],
        "subnet_second_part": [168],
        "subnet_third_part": [1],
    }
    result = read_data_from_yaml(data)
    expected = (
        ["nginx", "redis"],
        ["user1", "user2"],
        ["/path/to/key"],
        ["admin@10.0.0.0", "ubuntu@10.20.30.101"],
        192,
        168,
        1,
    )
    assert result == expected


def test_missing_field():
    data = {
        "containers": ["nginx"],
        "users": ["user1"],
        "identityFile": ["/path/to/key"],
        "hosts": ["ubuntu@10.20.30.101"],
        "subnet_first_part": ["192"],
        "subnet_second_part": ["168"],
        # 'subnet_third_part' is missing
    }
    with pytest.raises(
        ValueError, match="Missing subnet_third_part field in YAML data"
    ):
        read_data_from_yaml(data)


def test_empty_lists():
    data = {
        "containers": ["switch"],
        "users": [],
        "identityFile": [],
        "hosts": [],
        "subnet_first_part": [],
        "subnet_second_part": [],
        "subnet_third_part": [],
    }
    with pytest.raises(ValueError, match="Expected 'users' to be a non-empty list"):
        read_data_from_yaml(data)


def test_empty_subnet_field():
    data = {
        "containers": ["switch"],
        "users": ["mg234"],
        "identityFile": ["/home/nick/Data"],
        "hosts": ["ubuntu@10.20.30.103"],
        "subnet_first_part": [],
        "subnet_second_part": [2],
        "subnet_third_part": [3],
    }
    with pytest.raises(
        ValueError, match="Expected 'subnet_first_part' to be a non-empty list"
    ):
        read_data_from_yaml(data)


def test_incorrect_data_type():
    data = {
        "containers": "nginx",  # Should be a list
        "users": "user1",  # Should be a list
        "identityFile": ["/path/to/key"],  # Correct type but for completeness
        "hosts": "ubuntu@10.20.30.101",  # Should be a list
        "subnet_first_part": 192,  # Should be a list containing an int
        "subnet_second_part": 168,  # Should be a list containing an int
        "subnet_third_part": 1,  # Should be a list containing an int
    }
    with pytest.raises(ValueError, match="Expected 'containers' to be a list"):
        read_data_from_yaml(data)


def test_subnet_part_contains_multiple_values():
    data = {
        "containers": ["nginx"],
        "users": ["user1"],
        "identityFile": ["/path/to/key"],
        "hosts": ["ubuntu@10.20.30.101"],
        "subnet_first_part": [192, 193],  # More than one value
        "subnet_second_part": [168],
        "subnet_third_part": [1],
    }
    with pytest.raises(
        ValueError, match="Expected 'subnet_first_part' to contain exactly one value"
    ):
        read_data_from_yaml(data)


def test_subnet_part_non_integer_value():
    data = {
        "containers": ["nginx"],
        "users": ["user1"],
        "identityFile": ["/path/to/key"],
        "hosts": ["ubuntu@10.20.30.101"],
        "subnet_first_part": ["123a"],  # Non-integer value
        "subnet_second_part": [168],
        "subnet_third_part": [1],
    }
    with pytest.raises(
        ValueError, match="Expected 'subnet_first_part' to contain an integer value"
    ):
        read_data_from_yaml(data)


def test_extra_fields():
    data = {
        "containers": ["nginx"],
        "users": ["user1"],
        "identityFile": ["/path/to/key"],
        "hosts": ["ubuntu@10.20.30.101"],
        "subnet_first_part": [192],
        "subnet_second_part": [168],
        "subnet_third_part": [1],
        "extra_field": "extra_value",  # Extraneous field
    }
    result = read_data_from_yaml(data)
    expected = (
        ["nginx"],
        ["user1"],
        ["/path/to/key"],
        ["ubuntu@10.20.30.101"],
        192,
        168,
        1,
    )
    assert result == expected


def test_invalid_host_format():
    data = {
        "containers": ["nginx"],
        "users": ["user1"],
        "identityFile": ["path/to/key"],
        "hosts": ["ubuntu@10.20.30.104", "invalid-host"],
        "subnet_first_part": ["192"],
        "subnet_second_part": ["168"],
        "subnet_third_part": ["1"],
    }
    with pytest.raises(
        ValueError,
        match="Expected 'hosts' entries to be in the format 'username@ip_address', but got 'invalid-host'",
    ):
        read_data_from_yaml(data)
