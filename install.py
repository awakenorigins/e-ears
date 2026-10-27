#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E-Ears Installer — Auto-install dependencies and verify setup.

Usage:
    python install.py           # Install all dependencies
    python install.py --check   # Check if everything is installed
    python install.py --test    # Run quick test after install
"""

import subprocess
import sys
import os
import shutil


REQUIRED_PACKAGES = [
    ('librosa', '0.11.0'),
    ('soundfile', '0.13.0'),
    ('numpy', '1.26.0'),
    ('scipy', '1.17.0'),
]

OPTIONAL_PACKAGES = [
    ('openai-whisper', None),  # For lyrics transcription
]


def get_python():
    """Get the current Python executable."""
    return sys.executable


def check_package(name, min_version=None):
    """Check if a package is installed and meets version requirement."""
    try:
        mod = __import__(name.replace('-', '_'))
        version = getattr(mod, '__version__', 'unknown')
        if min_version and version != 'unknown':
            from packaging.version import Version
            if Version(version) < Version(min_version):
                return False, version, f'need >= {min_version}'
        return True, version, 'OK'
    except ImportError:
        return False, None, 'NOT INSTALLED'
    except Exception:
        # packaging might not be installed
        return True, 'unknown', 'OK (version unchecked)'


def install_packages(packages, optional=False):
    """Install packages via pip."""
    python = get_python()
    failed = []
    
    for name, min_ver in packages:
        installed, version, status = check_package(name, min_ver)
        if installed:
            print(f"  ✅ {name} {version}")
            continue
        
        print(f"  📦 Installing {name}...", end=' ', flush=True)
        try:
            result = subprocess.run(
                [python, '-m', 'pip', 'install', '--quiet', name],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                print("OK")
            else:
                if optional:
                    print(f"SKIP (optional)")
                else:
                    print(f"FAILED")
                    failed.append(name)
        except subprocess.TimeoutExpired:
            print("TIMEOUT")
            failed.append(name)
    
    return failed


def check_whisper():
    """Check if Whisper CLI is available."""
    whisper = shutil.which('whisper')
    if whisper:
        return True, whisper
    
    # Check common paths
    common_paths = [
        os.path.expanduser('~/.local/bin/whisper'),
        os.path.join(os.path.dirname(sys.executable), 'whisper'),
        os.path.join(os.path.dirname(sys.executable), 'Scripts', 'whisper.exe'),
    ]
    for p in common_paths:
        if os.path.isfile(p):
            return True, p
    
    return False, None


def run_check():
    """Check all dependencies."""
    print("🦻 E-Ears Dependency Check")
    print("=" * 40)
    
    all_ok = True
    
    print("\nRequired:")
    for name, min_ver in REQUIRED_PACKAGES:
        installed, version, status = check_package(name, min_ver)
        icon = "✅" if installed else "❌"
        ver_str = f" {version}" if version else ""
        print(f"  {icon} {name}{ver_str} — {status}")
        if not installed:
            all_ok = False
    
    print("\nOptional:")
    has_whisper, whisper_path = check_whisper()
    icon = "✅" if has_whisper else "⚠️"
    loc = f" ({whisper_path})" if whisper_path else ""
    print(f"  {icon} whisper{loc}")
    
    print("\nPython:", sys.version.split()[0])
    print("Platform:", sys.platform)
    
    if all_ok:
        print("\n✅ All required dependencies OK!")
    else:
        print("\n❌ Missing dependencies. Run: python install.py")
    
    return all_ok


def run_test():
    """Run a quick smoke test."""
    print("\n🧪 Running smoke test...")
    
    try:
        import librosa
        import numpy as np
        
        # Generate a simple test signal (440Hz sine wave, 3 seconds)
        sr = 22050
        duration = 3.0
        t = np.linspace(0, duration, int(sr * duration))
        y = 0.5 * np.sin(2 * np.pi * 440 * t)
        
        # Test feature extraction
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from scripts.core.features import detect_bpm, detect_key
        from scripts.core.mood import classify_mood
        
        bpm_data = detect_bpm(y, sr)
        key_data = detect_key(y, sr)
        print(f"  BPM detection: {bpm_data['bpm']} — {'OK' if bpm_data['bpm'] > 0 else 'FAIL'}")
        print(f"  Key detection: {key_data['key']} — OK")
        
        # Test mood
        features = {'bpm': bpm_data['bpm'], 'key_mode': key_data['mode'], 
                     'rms_energy': {'mean': 0.05}, 'spectral': {'spectral_centroid': {'mean': 2000}},
                     'hnr': {'hnr_db': 20}}
        mood = classify_mood(features)
        print(f"  Mood classify: {mood['mood']} — OK")
        
        print("\n✅ Smoke test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Smoke test FAILED: {e}")
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description='E-Ears Installer')
    parser.add_argument('--check', action='store_true', help='Check dependencies only')
    parser.add_argument('--test', action='store_true', help='Run smoke test')
    args = parser.parse_args()
    
    if args.check:
        run_check()
        return
    
    if args.test:
        run_check()
        run_test()
        return
    
    # Full install
    print("🦻 E-Ears Installer v1.0")
    print("=" * 40)
    
    print("\n📦 Installing required packages...")
    failed = install_packages(REQUIRED_PACKAGES)
    
    print("\n📦 Installing optional packages...")
    install_packages(OPTIONAL_PACKAGES, optional=True)
    
    if failed:
        print(f"\n❌ Failed to install: {', '.join(failed)}")
        print("Try manually: pip install " + ' '.join(failed))
        sys.exit(1)
    
    # Verify
    print()
    all_ok = run_check()
    
    if all_ok and args.test:
        run_test()
    
    if all_ok:
        print("\n🎉 E-Ears installed successfully!")
        print("Usage: python scripts/ears.py quick <file.mp3>")


if __name__ == '__main__':
    main()
