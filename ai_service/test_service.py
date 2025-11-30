"""Test script to verify model loading and basic functionality."""

from ai_service.core.model import FloodClassifier
from ai_service.utils import preprocess_image
from PIL import Image
import numpy as np

print("="*60)
print("Testing AI Service Components")
print("="*60)

# Test 1: Model Loading
print("\n[1] Testing model loading...")
try:
    model = FloodClassifier()
    info = model.get_model_info()
    print("[OK] Model loaded successfully")
    print(f"  Input: {info['input_name']} {info['input_shape']}")
    print(f"  Output: {info['output_name']} {info['output_shape']}")
    print(f"  Classes: {info['class_labels']}")
    print(f"  Threshold: {info['confidence_threshold']}")
except Exception as e:
    print(f"[FAIL] Model loading failed: {e}")
    exit(1)

# Test 2: Image Preprocessing
print("\n[2] Testing image preprocessing...")
try:
    # Create a dummy image
    test_image = Image.new('RGB', (640, 480), color='blue')
    preprocessed = preprocess_image(test_image)
    
    print(f"[OK] Preprocessing successful")
    print(f"  Output shape: {preprocessed.shape}")
    print(f"  Data type: {preprocessed.dtype}")
    print(f"  Value range: [{preprocessed.min():.3f}, {preprocessed.max():.3f}]")
    
    # Verify shape
    assert preprocessed.shape == (1, 3, 224, 224), f"Wrong shape: {preprocessed.shape}"
    assert preprocessed.dtype == np.float32, f"Wrong dtype: {preprocessed.dtype}"
    print("[OK] Shape and dtype validation passed")
except Exception as e:
    print(f"[FAIL] Preprocessing failed: {e}")
    exit(1)

# Test 3: Prediction
print("\n[3] Testing prediction...")
try:
    result = model.predict(preprocessed)
    
    print("[OK] Prediction successful")
    print(f"  Predicted class: {result['predicted_label']} (ID: {result['predicted_class']})")
    print(f"  Confidence: {result['confidence']:.4f}")
    print(f"  Confident: {result['confident']}")
    print(f"  Probabilities:")
    for label, prob in result['probabilities'].items():
        print(f"    - {label}: {prob:.4f}")
except Exception as e:
    print(f"[FAIL] Prediction failed: {e}")
    exit(1)

# Test 4: Softmax calculation
print("\n[4] Testing softmax calculation...")
try:
    # Verify softmax probabilities sum to 1
    total_prob = sum(result['probabilities'].values())
    assert abs(total_prob - 1.0) < 0.0001, f"Probabilities don't sum to 1: {total_prob}"
    print(f"[OK] Softmax validation passed (sum = {total_prob:.6f})")
except Exception as e:
    print(f"[FAIL] Softmax validation failed: {e}")
    exit(1)

print("\n" + "="*60)
print("All tests passed successfully! [OK]")
print("="*60)
