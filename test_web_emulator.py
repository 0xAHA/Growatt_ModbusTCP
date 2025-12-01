#!/usr/bin/env python3
"""
Test script to verify web emulator can load models without pymodbus
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing web emulator model loading...")
print("=" * 60)

try:
    # Import models module directly
    import importlib.util

    _models_spec = importlib.util.spec_from_file_location(
        'emulator_models',
        os.path.join(os.path.dirname(__file__), 'emulator', 'models.py')
    )
    _models_module = importlib.util.module_from_spec(_models_spec)
    _models_spec.loader.exec_module(_models_module)

    get_available_models = _models_module.get_available_models
    INVERTER_PROFILES = _models_module.INVERTER_PROFILES

    print("✓ Models module loaded successfully")

    # Get models
    models = get_available_models()
    print(f"✓ Found {len(models)} total models")

    # Filter out V2.01
    filtered = [k for k in models.keys() if '_v201' not in k]
    print(f"✓ {len(filtered)} models for web UI (excluding V2.01)")

    # Group by series
    def get_series(name):
        name_upper = name.upper()
        if 'MIC' in name_upper:
            return 'MIC'
        elif 'MIN' in name_upper:
            return 'MIN'
        elif 'TL-XH' in name_upper or 'TL XH' in name_upper:
            return 'TL-XH'
        elif 'MID' in name_upper:
            return 'MID'
        elif 'SPH-TL3' in name_upper or 'SPH TL3' in name_upper:
            return 'SPH-TL3'
        elif 'SPH' in name_upper:
            return 'SPH'
        elif 'MOD' in name_upper:
            return 'MOD'
        else:
            return 'Other'

    series_count = {}
    for key in filtered:
        profile = INVERTER_PROFILES[key]
        series = get_series(profile['name'])
        series_count[series] = series_count.get(series, 0) + 1

    print("\nModels by series:")
    for series in ['MIC', 'MIN', 'TL-XH', 'MID', 'SPH', 'SPH-TL3', 'MOD', 'Other']:
        if series in series_count:
            print(f"  {series:10} {series_count[series]} models")

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("\nYou can now run the web emulator:")
    print("  python3 growatt_emulator_web.py --webport 8080")
    print("\nNote: You'll need Flask to run the web server:")
    print("  pip install Flask flask-cors")
    print("\nTo actually start an emulator, you'll also need:")
    print("  pip install pymodbus rich")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
