import subprocess
import sys

packages = [
    'pandas',
    'numpy',
    'matplotlib',
    'seaborn',
    'scikit-learn',
    'xgboost',
    'lightgbm',
    'scipy',
    'flask',
    'flask-cors',
    'requests',
    'python-dotenv',
    'plotly',
    'folium',
    'geopy',
    'sqlalchemy',
    'pytz',
    'Werkzeug',
    'APScheduler',
]

print("="*70)
print("INSTALLING PACKAGES")
print("="*70)

for i, package in enumerate(packages, 1):
    print(f"\n[{i}/{len(packages)}] Installing: {package}")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '--upgrade'])
        print(f"✓ {package} installed")
    except:
        print(f"✗ {package} failed")

print("\n" + "="*70)
print("Installation complete!")
print("="*70)