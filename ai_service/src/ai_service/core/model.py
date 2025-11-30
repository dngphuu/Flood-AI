"""
Core model module for flood image classification.

This module provides the FloodClassifier class that handles ONNX model loading
and inference without any PyTorch dependencies.
"""

import numpy as np
import onnxruntime as ort
from typing import Dict, Tuple
import logging

from ai_service.config import (
    MODEL_PATH,
    CLASS_LABELS,
    CONFIDENCE_THRESHOLD,
    INPUT_SHAPE
)

logger = logging.getLogger(__name__)


class FloodClassifier:
    """
    Flood image classifier using ONNX Runtime.
    
    This class handles loading the ONNX model (including external weights)
    and performing inference on preprocessed images.
    
    Attributes:
        model_path: Path to the ONNX model file
        session: ONNX Runtime inference session
        input_name: Name of the model's input tensor
        output_name: Name of the model's output tensor
    """
    
    def __init__(self):
        """
        Initialize the FloodClassifier.
        
        Loads the ONNX model from the configured path. The model should have
        external weights stored in a separate .onnx.data file in the same directory.
        
        Raises:
            FileNotFoundError: If model file doesn't exist
            RuntimeError: If model loading fails
        """
        self.model_path = MODEL_PATH
        
        # Verify model file exists
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model file not found at {self.model_path}. "
                f"Please ensure both {self.model_path.name} and "
                f"{self.model_path.name}.data are present in the models directory."
            )
        
        logger.info(f"Loading ONNX model from {self.model_path}")
        
        try:
            # Create ONNX Runtime session
            # The session will automatically load external weights from .onnx.data
            # if it's in the same directory as the .onnx file
            session_options = ort.SessionOptions()
            session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            # Use CPU provider (no CUDA dependencies)
            providers = ['CPUExecutionProvider']
            
            self.session = ort.InferenceSession(
                str(self.model_path),
                sess_options=session_options,
                providers=providers
            )
            
            # Get input and output names
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
            
            # Validate input shape
            expected_shape = self.session.get_inputs()[0].shape
            logger.info(f"Model input shape: {expected_shape}")
            logger.info(f"Model output name: {self.output_name}")
            logger.info("Model loaded successfully")
            
        except Exception as e:
            error_msg = f"Failed to load ONNX model: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    @staticmethod
    def _softmax(logits: np.ndarray) -> np.ndarray:
        """
        Compute softmax probabilities from raw logits.
        
        Uses numerical stability trick by subtracting the max value before
        exponentiating to prevent overflow.
        
        Args:
            logits: Raw model outputs (logits), shape (batch_size, num_classes)
        
        Returns:
            np.ndarray: Softmax probabilities, shape (batch_size, num_classes)
        
        Example:
            >>> logits = np.array([[2.0, 1.0]])
            >>> probs = FloodClassifier._softmax(logits)
            >>> print(probs)  # [[0.731, 0.269]]
        """
        # Subtract max for numerical stability
        logits_max = np.max(logits, axis=-1, keepdims=True)
        exp_logits = np.exp(logits - logits_max)
        
        # Normalize to get probabilities
        probabilities = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)
        
        return probabilities
    
    def predict(self, preprocessed_image: np.ndarray) -> Dict:
        """
        Perform inference on a preprocessed image.
        
        Args:
            preprocessed_image: Preprocessed image array with shape (1, 3, 224, 224)
        
        Returns:
            Dict containing:
                - predicted_class (int): Predicted class index (0 or 1)
                - predicted_label (str): Class label ("dry_road" or "flood")
                - confidence (float): Confidence score for the predicted class
                - probabilities (dict): Probabilities for all classes
                - confident (bool): Whether prediction meets confidence threshold
                - threshold (float): The confidence threshold used
        
        Raises:
            ValueError: If input shape is incorrect
            RuntimeError: If inference fails
        
        Example:
            >>> classifier = FloodClassifier()
            >>> from ai_service.utils import preprocess_image
            >>> preprocessed = preprocess_image("image.jpg")
            >>> result = classifier.predict(preprocessed)
            >>> print(result["predicted_label"])  # "flood" or "dry_road"
        """
        # Validate input shape
        if preprocessed_image.shape != INPUT_SHAPE:
            raise ValueError(
                f"Invalid input shape {preprocessed_image.shape}. "
                f"Expected {INPUT_SHAPE}"
            )
        
        try:
            # Run inference
            logger.debug(f"Running inference with input shape: {preprocessed_image.shape}")
            
            outputs = self.session.run(
                [self.output_name],
                {self.input_name: preprocessed_image}
            )
            
            # Get logits (raw model outputs)
            logits = outputs[0]  # Shape: (1, num_classes)
            
            # Compute softmax probabilities
            probabilities = self._softmax(logits)  # Shape: (1, num_classes)
            
            # Get predictions for the first (and only) batch item
            probs = probabilities[0]  # Shape: (num_classes,)
            
            # Get predicted class (argmax)
            predicted_class = int(np.argmax(probs))
            
            # Get confidence (probability of the predicted class)
            confidence = float(probs[predicted_class])
            
            # Get class label
            predicted_label = CLASS_LABELS[predicted_class]
            
            # Check if prediction meets confidence threshold
            confident = confidence >= CONFIDENCE_THRESHOLD
            
            # Build probabilities dictionary
            probs_dict = {
                CLASS_LABELS[i]: float(probs[i])
                for i in range(len(probs))
            }
            
            logger.info(
                f"Prediction: {predicted_label} "
                f"(confidence: {confidence:.4f}, "
                f"threshold: {CONFIDENCE_THRESHOLD})"
            )
            
            return {
                "predicted_class": predicted_class,
                "predicted_label": predicted_label,
                "confidence": confidence,
                "probabilities": probs_dict,
                "confident": confident,
                "threshold": CONFIDENCE_THRESHOLD
            }
            
        except Exception as e:
            error_msg = f"Inference failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def get_model_info(self) -> Dict:
        """
        Get information about the loaded model.
        
        Returns:
            Dict containing model metadata like input/output names and shapes
        """
        return {
            "model_path": str(self.model_path),
            "input_name": self.input_name,
            "output_name": self.output_name,
            "input_shape": self.session.get_inputs()[0].shape,
            "output_shape": self.session.get_outputs()[0].shape,
            "providers": self.session.get_providers(),
            "class_labels": CLASS_LABELS,
            "confidence_threshold": CONFIDENCE_THRESHOLD
        }
