#!/usr/bin/env python3
"""Check MATLAB engine module attributes"""
import sys
sys.path.insert(0, "E:/NEMT Simulator")

import matlab.engine
print(f"matlab.engine module: {matlab.engine}")
print(f"Available attributes: {dir(matlab.engine)}")
print()

# Check if startMATLAB exists
if hasattr(matlab.engine, 'startMATLAB'):
    print("startMATLAB: FOUND")
else:
    print("startMATLAB: NOT FOUND")
    print("Available functions starting with 'start':")
    for attr in dir(matlab.engine):
        if 'start' in attr.lower():
            print(f"  - {attr}")
