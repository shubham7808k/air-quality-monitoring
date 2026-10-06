#!/usr/bin/env python
"""Verify all required packages are installed correctly"""

import sys

print(f"Python Version: {sys.version}")
print("\n" + "="*70)
print("VERIFYING PACKAGE INSTALLATIONS FOR AQI MONITORING SYSTEM")
print("="*70 + "\n")

packages = {
    'pandas': 'Data Processing',
    'numpy': 'Numerical Computing',
    'matplotlib': 'Plotting',
    'seaborn': 'Statistical Visualization',
    'sklearn': 'Machine Learning',
    'xgboost': 'Gradient Boosting',
    'lightgbm': 'Light Gradient Boosting',
    'scipy': 'Scientific Computing',
    'tensorflow': 'Deep Learning',
    'flask': 'Web Framework',
    'flask_cors': 'Flask CORS',
    'requests': 'HTTP Requests',
    'dotenv': 'Environment Variables',
    'plotly': 'Interactive Plotting',
    'folium': 'Maps',
    'geopy': 'Geolocation',
    'sqlalchemy': 'Database ORM',
    'pytz': 'Timezone',
    'werkzeug': 'WSGI Utilities',
    'apscheduler': 'Task Scheduling',
    'jupyter': 'Jupyter Notebook',
    'IPython': 'IPython Shell'
}

success_count = 0
failed_packages = []

for package_name, description in packages.items():
    try:
        module = __import__(package_name)
        version = getattr(module, '__version__', 'Unknown')
        status = f"✓ {package_name:20} v{version:15} - {description}"
        print(status)
        success_count += 1
    except ImportError as e:
        status = f"✗ {package_name:20} NOT INSTALLED      - {description}"
        print(status)
        failed_packages.append(package_name)

print("\n" + "="*70)
print(f"SUMMARY: {success_count}/{len(packages)} packages installed successfully")
print("="*70)

if failed_packages:
    print(f"\n❌ Failed packages: {', '.join(failed_packages)}")
    print("\nFix with:")
    for pkg in failed_packages:
        print(f"  pip install {pkg}")
    sys.exit(1)
else:
    print("\n✅ ALL PACKAGES INSTALLED SUCCESSFULLY!")
    print("\n" + "="*70)
    print("Your environment is ready to start the project!")
    print("="*70)
    sys.exit(0)