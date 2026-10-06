"""Quick test to verify the setup is working"""

import os
import sys
from datetime import datetime

print("\n" + "="*70)
print("AIR QUALITY MONITORING SYSTEM - SETUP TEST")
print("="*70 + "\n")

# Test 1: Check Python version
print(f"✓ Python Version: {sys.version.split()[0]}")

# Test 2: Check directories
required_dirs = [
    'backend',
    'frontend',
    'data',
    'logs',
    'static',
    'templates'
]

print("\n✓ Directory Structure:")
for dir_name in required_dirs:
    if os.path.exists(dir_name):
        print(f"  ✓ {dir_name}/ exists")
    else:
        print(f"  ✗ {dir_name}/ MISSING - creating...")
        os.makedirs(dir_name, exist_ok=True)

# Test 3: Import key libraries
print("\n✓ Importing Libraries:")

try:
    import pandas as pd
    print(f"  ✓ pandas {pd.__version__}")
except Exception as e:
    print(f"  ✗ pandas ERROR: {e}")

try:
    import numpy as np
    print(f"  ✓ numpy {np.__version__}")
except Exception as e:
    print(f"  ✗ numpy ERROR: {e}")

try:
    import sklearn
    print(f"  ✓ scikit-learn {sklearn.__version__}")
except Exception as e:
    print(f"  ✗ scikit-learn ERROR: {e}")

try:
    import flask
    print(f"  ✓ flask {flask.__version__}")
except Exception as e:
    print(f"  ✗ flask ERROR: {e}")

try:
    import tensorflow as tf
    print(f"  ✓ tensorflow {tf.__version__}")
except Exception as e:
    print(f"  ✗ tensorflow ERROR: {e}")
    print("     (This is optional - you can continue without it)")

# Test 4: Check if config.py exists
print("\n✓ Configuration Files:")
if os.path.exists('config.py'):
    print(f"  ✓ config.py exists")
else:
    print(f"  ✗ config.py NOT FOUND - you'll need to create it")

print("\n" + "="*70)
print("SETUP TEST COMPLETE!")
print("="*70 + "\n")