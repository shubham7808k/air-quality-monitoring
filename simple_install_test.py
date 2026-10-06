"""Simple test to check if basic packages can be imported"""

print("\n" + "="*60)
print("CHECKING PACKAGE INSTALLATIONS")
print("="*60 + "\n")

packages_to_test = [
    ('pandas', 'Data Processing'),
    ('numpy', 'Numerical Computing'),
    ('matplotlib', 'Plotting'),
    ('sklearn', 'Machine Learning'),
    ('flask', 'Web Framework'),
]

success = 0
failed = 0

for package_name, description in packages_to_test:
    try:
        __import__(package_name)
        print(f"✓ {package_name:20} - {description}")
        success += 1
    except ImportError:
        print(f"✗ {package_name:20} - NOT INSTALLED")
        failed += 1

print("\n" + "="*60)
print(f"Result: {success} installed, {failed} failed")
print("="*60 + "\n")

if failed == 0:
    print("✅ BASIC SETUP SUCCESSFUL!")
else:
    print(f"⚠️  Please install missing packages")