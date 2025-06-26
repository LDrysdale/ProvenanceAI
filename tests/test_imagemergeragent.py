import os
import pytest
from PIL import Image
import numpy as np
from unittest.mock import patch
from agents.imagemergeragent import ImageMergeAgent

TEST_IMAGE_DIR = "tests/images"
os.makedirs(TEST_IMAGE_DIR, exist_ok=True)

def create_test_image(path, size=(512, 512), color=(255, 0, 0)):
    image = Image.new("RGB", size, color=color)
    image.save(path)

@pytest.fixture(scope="module")
def dummy_images():
    paths = []
    for i in range(3):
        path = os.path.join(TEST_IMAGE_DIR, f"test_img_{i}.png")
        create_test_image(path, size=(512, 512), color=(i*50, i*50, 255 - i*50))
        paths.append(path)
    return paths

def test_valid_image_sizes(dummy_images):
    agent = ImageMergeAgent()
    for path in dummy_images:
        img = Image.open(path)
        assert 256 <= img.width <= 2048
        assert 256 <= img.height <= 2048

def test_invalid_image_size():
    path = os.path.join(TEST_IMAGE_DIR, "invalid_img.png")
    create_test_image(path, size=(100, 100))
    agent = ImageMergeAgent()
    with pytest.raises(ValueError, match="Image size must be between 256x256 and 2048x2048"):
        agent.merge_images([path, path], "merge image1 and image2")

def test_prompt_parsing_with_weights(dummy_images):
    prompt = "Combine image1:0.6 and image2:0.4 using their best features."
    agent = ImageMergeAgent()
    weights = agent._parse_image_weights(prompt, len(dummy_images))
    assert weights == {0: 0.6, 1: 0.4}

def test_prompt_parsing_without_weights(dummy_images):
    prompt = "Please merge image1, image2, and image3 into one."
    agent = ImageMergeAgent()
    weights = agent._parse_image_weights(prompt, len(dummy_images))
    assert sum(weights.values()) == pytest.approx(1.0)
    assert len(weights) == 3

@patch.object(ImageMergeAgent, '_generate_mask', return_value=np.ones((512, 512), dtype=bool))
@patch.object(ImageMergeAgent, '_refine_with_diffusion', return_value=Image.new("RGB", (1024, 1024)))
def test_successful_merge(mock_refine, mock_mask, dummy_images):
    agent = ImageMergeAgent()
    result = agent.merge_images(
        dummy_images[:3],
        "Merge image1, image2, and image3 with a soft blend.",
        output_path=os.path.join(TEST_IMAGE_DIR, "test_output.png")
    )
    assert result.size == (1024, 1024)
