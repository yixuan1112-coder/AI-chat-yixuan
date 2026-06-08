#!/usr/bin/env python3
"""
Step 0: Explore Oxford Battery Degradation Dataset structure.
Run this FIRST after downloading the raw data to confirm .mat file structure.

Usage:
    conda activate batterytwin
    cd ~/Projects/BatteryTwin-Benchmark-DataPrep
    python scripts/explore_oxford.py
"""

import os
import sys

# ============================================================
# Part A: Kokam LCO Dataset 1
# ============================================================
KOKAM_PATH = "data/raw/dataset_04_Oxford/kokam_lco/Oxford_Battery_Degradation_Dataset_1.mat"

print("=" * 70)
print("PART A: Kokam LCO - Oxford Battery Degradation Dataset 1")
print("=" * 70)

if not os.path.exists(KOKAM_PATH):
    print(f"[SKIP] File not found: {KOKAM_PATH}")
    print("       Download it first, see DOWNLOAD.md")
else:
    # Try scipy first (MATLAB v5), fall back to h5py (MATLAB v7.3/HDF5)
    try:
        import scipy.io as sio
        data = sio.loadmat(KOKAM_PATH)
        print("[INFO] Loaded with scipy.io.loadmat (MATLAB v5 format)")
        print(f"\nTop-level keys: {[k for k in data.keys() if not k.startswith('__')]}")
        
        for key in sorted(data.keys()):
            if key.startswith('__'):
                continue
            obj = data[key]
            print(f"\n--- Key: {key} ---")
            print(f"  Type: {type(obj)}, Shape: {getattr(obj, 'shape', 'N/A')}, Dtype: {getattr(obj, 'dtype', 'N/A')}")
            
            # If structured array, show field names
            if hasattr(obj, 'dtype') and obj.dtype.names:
                print(f"  Fields: {obj.dtype.names}")
                # Go one level deeper
                for field in obj.dtype.names[:5]:  # limit to 5
                    sub = obj[field]
                    print(f"    [{field}] type={type(sub)}, shape={getattr(sub, 'shape', 'N/A')}")
                    if hasattr(sub, 'dtype') and sub.dtype.names:
                        print(f"    [{field}] sub-fields: {sub.dtype.names}")
            
            # If it's a cell array of structs, navigate
            if hasattr(obj, 'flat'):
                first = obj.flat[0]
                if hasattr(first, 'dtype') and first.dtype.names:
                    print(f"  [0] sub-fields: {first.dtype.names}")
                    for sf in first.dtype.names[:5]:
                        inner = first[sf]
                        print(f"    [{sf}] shape={getattr(inner, 'shape', 'N/A')}")
    
    except NotImplementedError:
        print("[INFO] scipy failed → trying h5py (MATLAB v7.3 / HDF5 format)")
        import h5py
        with h5py.File(KOKAM_PATH, 'r') as f:
            print(f"\nTop-level keys: {list(f.keys())}")
            
            def explore_h5(group, prefix="", depth=0, max_depth=4):
                if depth > max_depth:
                    return
                for key in list(group.keys())[:8]:  # limit breadth
                    item = group[key]
                    indent = "  " * (depth + 1)
                    if isinstance(item, h5py.Group):
                        print(f"{indent}{prefix}{key}/ ({len(item)} items)")
                        explore_h5(item, f"{prefix}{key}/", depth + 1, max_depth)
                    elif isinstance(item, h5py.Dataset):
                        print(f"{indent}{prefix}{key}: shape={item.shape}, dtype={item.dtype}")
                    if depth == 0 and key != list(group.keys())[-1]:
                        print()
            
            explore_h5(f)

print()

# ============================================================
# Part B: NCA 18650 Path Dependent Dataset
# ============================================================
NCA_DIR = "data/raw/dataset_04_Oxford/nca_18650/"

print("=" * 70)
print("PART B: NCA 18650 - Path Dependent Battery Degradation Dataset")
print("=" * 70)

if not os.path.isdir(NCA_DIR):
    print(f"[SKIP] Directory not found: {NCA_DIR}")
    print("       Download files first, see DOWNLOAD.md")
else:
    mat_files = sorted([f for f in os.listdir(NCA_DIR) if f.endswith('.mat')])
    print(f"\nFound {len(mat_files)} .mat files:")
    for f in mat_files:
        size_mb = os.path.getsize(os.path.join(NCA_DIR, f)) / 1e6
        print(f"  {f}  ({size_mb:.1f} MB)")
    
    if mat_files:
        # Explore first file
        first_file = os.path.join(NCA_DIR, mat_files[0])
        print(f"\n--- Exploring: {mat_files[0]} ---")
        
        try:
            import scipy.io as sio
            data = sio.loadmat(first_file)
            print("[INFO] Loaded with scipy.io.loadmat")
            keys = [k for k in data.keys() if not k.startswith('__')]
            print(f"Keys: {keys}")
            
            for key in keys[:3]:
                obj = data[key]
                print(f"\n  [{key}] type={type(obj)}, shape={getattr(obj, 'shape', 'N/A')}")
                if hasattr(obj, 'dtype'):
                    print(f"  dtype={obj.dtype}")
                    if obj.dtype.names:
                        print(f"  fields={obj.dtype.names}")
                # Show first few values if numeric
                if hasattr(obj, 'shape') and obj.size < 20:
                    print(f"  values={obj}")
        except NotImplementedError:
            import h5py
            print("[INFO] Using h5py (HDF5 format)")
            with h5py.File(first_file, 'r') as f:
                print(f"Keys: {list(f.keys())}")
                for key in list(f.keys())[:5]:
                    item = f[key]
                    if isinstance(item, h5py.Group):
                        print(f"  {key}/ → {list(item.keys())[:10]}")
                    elif isinstance(item, h5py.Dataset):
                        print(f"  {key}: shape={item.shape}, dtype={item.dtype}")

print("\n" + "=" * 70)
print("DONE. Copy the output above and paste it into Claude for next steps.")
print("=" * 70)
