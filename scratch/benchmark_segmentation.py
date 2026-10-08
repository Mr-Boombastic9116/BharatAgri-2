"""
Benchmark script: Compare Individual Mango Separation Candidates
1. SAM 2 feasibility check & evaluation
2. Marker-controlled Watershed + Euclidean Distance Transform (EDT)
3. Contour Concavity / Boundary Curvature Splitting
4. Hybrid (EDT Watershed + Concavity Notches + Boundary Edge Crease + Region Validation)
"""
import os
import sys
import time
import numpy as np
from PIL import Image, ImageDraw

def test_sam2_availability():
    print("=== SAM 2 FEASIBILITY TEST ===")
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}, CUDA available: {torch.cuda.is_available()}")
        try:
            import sam2
            print("SAM 2 package is installed.")
            return True
        except ImportError:
            print("SAM 2 package is NOT installed in the environment.")
            return False
    except ImportError:
        print("PyTorch is NOT installed in virtualenv (torch missing).")
        print("SAM 2 requires PyTorch, torchvision, and CUDA / substantial CPU compute (~1GB model weights).")
        print("Evaluation: SAM 2 is not viable for real-time edge/serverless inference without heavy dependencies and latency.")
        return False

if __name__ == "__main__":
    test_sam2_availability()
