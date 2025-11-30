"""
Image preprocessing utilities for flood classification.

This module provides functions to preprocess images using NumPy and PIL,
without any PyTorch dependencies.
"""

import numpy as np
from PIL import Image
from typing import Union, BinaryIO
import io

from ai_service.config import IMAGE_SIZE, IMAGENET_MEAN, IMAGENET_STD, INPUT_SHAPE


def preprocess_image(image_input: Union[str, BinaryIO, Image.Image]) -> np.ndarray:
    """
    Preprocess an image for model inference.
    
    This function performs the following steps:
    1. Load image using PIL
    2. Convert to RGB if needed
    3. Resize to 224x224 using bilinear interpolation
    4. Normalize using ImageNet mean and std
    5. Transpose from HWC to CHW format
    6. Add batch dimension
    7. Convert to float32
    
    Args:
        image_input: Can be:
            - str: Path to image file
            - BinaryIO: File-like object (e.g., from Flask request.files)
            - Image.Image: PIL Image object
    
    Returns:
        np.ndarray: Preprocessed image with shape (1, 3, 224, 224) and dtype float32
    
    Raises:
        ValueError: If image cannot be loaded or processed
        IOError: If file cannot be read
    
    Example:
        >>> from ai_service.utils.image_utils import preprocess_image
        >>> preprocessed = preprocess_image("path/to/image.jpg")
        >>> print(preprocessed.shape)  # (1, 3, 224, 224)
    """
    
    try:
        # Step 1: Load the image
        if isinstance(image_input, str):
            # Load from file path
            image = Image.open(image_input)
        elif isinstance(image_input, Image.Image):
            # Already a PIL Image
            image = image_input
        else:
            # Assume it's a file-like object (BinaryIO)
            # Read the binary content and create PIL Image
            image_bytes = image_input.read()
            image = Image.open(io.BytesIO(image_bytes))
        
        # Step 2: Convert to RGB (handles RGBA, grayscale, etc.)
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Step 3: Resize to target size (224x224) using bilinear interpolation
        # PIL.Image.BILINEAR is equivalent to torchvision's default interpolation
        image = image.resize(IMAGE_SIZE, Image.BILINEAR)
        
        # Step 4: Convert PIL Image to NumPy array (H, W, C) with values in [0, 255]
        image_array = np.array(image, dtype=np.float32)
        
        # Step 5: Normalize to [0, 1] by dividing by 255
        image_array = image_array / 255.0
        
        # Step 6: Normalize using ImageNet mean and std
        # Convert mean and std to numpy arrays for broadcasting
        mean = np.array(IMAGENET_MEAN, dtype=np.float32).reshape(1, 1, 3)
        std = np.array(IMAGENET_STD, dtype=np.float32).reshape(1, 1, 3)
        
        # Apply normalization: (image - mean) / std
        image_array = (image_array - mean) / std
        
        # Step 7: Transpose from HWC (Height, Width, Channels) to CHW (Channels, Height, Width)
        # This is the format expected by most deep learning models
        image_array = np.transpose(image_array, (2, 0, 1))
        
        # Step 8: Add batch dimension at the front: (C, H, W) -> (1, C, H, W)
        image_array = np.expand_dims(image_array, axis=0)
        
        # Step 9: Ensure the array is contiguous in memory and float32
        image_array = np.ascontiguousarray(image_array, dtype=np.float32)
        
        # Validate output shape
        expected_shape = INPUT_SHAPE
        if image_array.shape != expected_shape:
            raise ValueError(
                f"Preprocessed image has unexpected shape {image_array.shape}. "
                f"Expected {expected_shape}"
            )
        
        return image_array
    
    except Exception as e:
        raise ValueError(f"Failed to preprocess image: {str(e)}") from e


def validate_image_file(filename: str, allowed_extensions: set) -> bool:
    """
    Validate if a file has an allowed image extension.
    
    Args:
        filename: Name of the file to validate
        allowed_extensions: Set of allowed file extensions (without dot)
    
    Returns:
        bool: True if file extension is allowed, False otherwise
    
    Example:
        >>> validate_image_file("test.jpg", {"jpg", "png"})
        True
        >>> validate_image_file("test.txt", {"jpg", "png"})
        False
    """
    if not filename:
        return False
    
    # Get file extension (without the dot)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    
    return extension in allowed_extensions
