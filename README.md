# Orbital System Simulation

A modular, high-performance 2D N-body gravitational physics simulation built in Python and Pygame, accelerated with a custom C++ native engine.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![C++](https://img.shields.io/badge/C++-17-00599C?style=flat&logo=cplusplus&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-2.6-green?style=flat)

---

## Key Features

- **4th-Order Runge-Kutta (RK4) Integration**: High-precision numerical differential equation solver for accurate long-term orbital stability[cite: 12, 16].
- **Hybrid C++/Python Physics Engine**:
  - Pure Python physics engine fallback for universal cross-platform compatibility.
  - Native C++ acceleration (`physics.dll` / `.so`) delivering **50x–100x speedups** for large body counts[cite: 12, 18].
- **Specialized Body Mechanics**:
  - **Stars**: Dynamic stellar evolution color shifting (Yellow -> Red Giant -> White Dwarf) with cache-quantized visual radial glows[cite: 21].
  - **Black Holes**: Event horizon gravitational accretion, body absorption, and real-time merger logic[cite: 21].
  - **Planets & Moons**: Realistic shadows calculated relative to nearest stars and continuous trail rendering[cite: 21].
- **Inelastic Collision & Conservation of Momentum**: Fully resolved mass, momentum, and volumetric merging with particle explosion effects[cite: 16, 17, 19].
- **Interactive GUI Spawning**: On-the-fly "slingshot" drag-and-launch system to spawn planets, stars, or black holes live during runtime[cite: 17].
- **Smooth Dynamic Center-of-Mass Camera**: Automated tracking relative to total system barycenter with zoom controls[cite: 17].

---

## Prerequisites

Before running or compiling the simulation, ensure your system meets the following requirements:

1. **Python**: Version `3.8` or higher[cite: 18].
2. **Pygame**: Version `2.0` or higher (`pip install pygame`)[cite: 17].
3. **C++ Compiler (`g++`)** *(Required only for compiling the native C++ acceleration library)*:
   - **Windows**: [MinGW-w64](https://www.mingw-w64.org/) or [MSYS2](https://www.msys2.org/) (ensure `g++` is added to system `PATH`).
   - **Linux**: Install via package manager (`sudo apt install build-essential g++`).
   - **macOS**: Install Xcode Command Line Tools (`xcode-select --install`).

---

## Controls 

| Input | Action |
| :--- | :--- |
| **Right-Click + Drag** | Aim velocity vector and launch selected celestial body[cite: 17] |
| **T** | Toggle spawn body type (*Planet* $\rightarrow$ *Star* $\rightarrow$ *BlackHole*)[cite: 17] |
| **`[` / `]`** | Decrease / Increase spawn body mass[cite: 17] |
| **`-` / `=`** | Decrease / Increase spawn body radius[cite: 17] |
| **Spacebar** | Pause / Resume physics simulation[cite: 17] |
| **Up / Down Arrows** | Increase / Decrease time step ($\Delta t$)[cite: 17] |
| **Mouse Wheel** | Zoom in / Zoom out[cite: 17] |
| **F11 / F** | Toggle Fullscreen mode[cite: 17] |

---

## 🚀 Native C++ Acceleration Performance

The physics loop supports dual execution[cite: 17, 18]. When compiled native libraries are present, `native_physics.py` automatically offloads calculation loops to C++[cite: 17, 18]:

| Body Count ($N$) | Python (`ms/frame`) | C++ Native (`ms/frame`) | Speedup |
| :--- | :--- | :--- | :--- |
| **25** | ~1.5 ms | ~0.02 ms | **~75x** |
| **100** | ~24.0 ms | ~0.25 ms | **~96x** |
| **400** | ~380.0 ms | ~3.80 ms | **~100x** |

To run the comparative benchmark suite locally[cite: 12]:
```bash
python bench.py
