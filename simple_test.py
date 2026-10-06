import sys

print("\n" + "="*60)
print("TESTING PACKAGE INSTALLATIONS")
print("="*60 + "\n")

packages = {
    'pandas': 'Data',
    'numpy': 'NumPy',
    'matplotlib': 'Plotting',
    'sklearn': 'ML',
    'flask': 'Web',
}

success = 0

for pkg, name in packages.items():
    try:
        __import__(pkg)
        print(f"✓ {name} ({pkg})")
        success += 1
    except:
        print(f"✗ {name} ({pkg}) - NOT INSTALLED")

print("\n" + "="*60)
print(f"Result: {success}/{len(packages)} packages working")
print("="*60 + "\n")

if success >= 4:
    print("✅ READY TO START!")
else:
    print("⚠️  Run: python install_packages.py")