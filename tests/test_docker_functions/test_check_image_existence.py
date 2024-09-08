import pytest
from unittest.mock import patch, MagicMock
import docker
from src.docker_functions import check_image_existence


# Test for an image that exists locally
@patch("docker.from_env")
def test_image_exists_locally(mock_from_env):
    mock_client = MagicMock()
    mock_from_env.return_value = mock_client
    mock_client.images.get.return_value = True  # Simulate image exists

    result = check_image_existence("local_image:latest")
    assert result is True
    mock_client.images.get.assert_called_once_with("local_image:latest")
    mock_client.images.pull.assert_not_called()


# Test for an image that does not exist locally but can be pulled
@patch("docker.from_env")
def test_image_pulled_successfully(mock_from_env):
    mock_client = MagicMock()
    mock_from_env.return_value = mock_client
    mock_client.images.get.side_effect = docker.errors.ImageNotFound(
        "Image not found locally"
    )  # Simulate image not found locally
    mock_client.images.pull.return_value = True  # Simulate successful pull

    result = check_image_existence("remote_image:latest")
    assert result is True
    mock_client.images.get.assert_called_once_with("remote_image:latest")
    mock_client.images.pull.assert_called_once_with("remote_image:latest")


# Test for an image that cannot be pulled
@patch("docker.from_env")
def test_image_cannot_be_pulled(mock_from_env):
    mock_client = MagicMock()
    mock_from_env.return_value = mock_client
    mock_client.images.get.side_effect = docker.errors.ImageNotFound(
        "Image not found locally"
    )  # Simulate image not found locally
    mock_client.images.pull.side_effect = docker.errors.ImageNotFound(
        "Image could not be pulled"
    )  # Simulate pull failure

    with pytest.raises(docker.errors.ImageNotFound):
        check_image_existence("non_existent_image:latest")
    mock_client.images.get.assert_called_once_with("non_existent_image:latest")
    mock_client.images.pull.assert_called_once_with("non_existent_image:latest")
