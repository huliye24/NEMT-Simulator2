# Copyright 2026 NEMT Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test script to verify NEMT Simulator"""
import sys
sys.path.insert(0, '.')

import numpy as np
from nemt_core import NEMTSimulator, NEMTParams
from visualizer import NEMTVisualizer

print("Generating demo data...")
np.random.seed(42)
t = np.linspace(0, 10, 200)
price = 2 * np.sin(0.5 * t) + 1.5 * np.sin(1.3 * t) + 0.3 * np.random.randn(200)

print("Initializing simulator...")
sim = NEMTSimulator(NEMTParams(alpha=0.1, beta=1.0, noise_level=0.2, steps=50))
psi = sim.initialize_state(price)

print("Running evolution...")
psi = sim.evolve(psi)

print("Spectral analysis...")
freqs, spectrum = sim.spectral_analysis(psi)
width = sim.compute_spectral_width()
resonance = sim.detect_resonance()

print(f"\nSpectral Width: {width:.6f}")
print(f"Resonance peaks: {resonance['num_peaks']}")

print("\nGenerating visualization...")
vis = NEMTVisualizer()
fig = vis.plot_spectrum(spectrum, freqs)
vis.save_figure(fig, "output/test_spectrum.png")

print("\nTest completed successfully!")
