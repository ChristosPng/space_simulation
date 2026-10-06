# Orbital System Simulation

A modular, high-performance 2D N-body gravitational physics simulation built in Python and Pygame, accelerated with a custom C++ native engine.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![C++](https://img.shields.io/badge/C++-17-00599C?style=flat&logo=cplusplus&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-2.6-green?style=flat)

---

## Key Features

- **4th-Order Runge-Kutta (RK4) Integration**: High-precision numerical differential equation solver for accurate long-term orbital stability.
- **Dynamic Texture Generation using Perlin Noise**
- **Hybrid C++/Python Physics Engine**:
  - Pure Python physics engine fallback for universal cross-platform compatibility.
  - Native C++ acceleration (`physics.dll` / `.so`) delivering **50x–100x speedups** for large body counts.
- **Specialized Body Mechanics**:
  - **Stars**: Dynamic stellar evolution color shifting (Yellow -> Red Giant -> White Dwarf) with cache-quantized visual radial glows.
  - **Black Holes**: Event horizon gravitational accretion, body absorption, and real-time merger logic.
  - **Planets & Moons**: Realistic shadows calculated relative to nearest stars and continuous trail rendering.
- **Inelastic Collision & Conservation of Momentum**: Fully resolved mass, momentum, and volumetric merging with particle explosion effects.
- **Interactive GUI Spawning**: On-the-fly "slingshot" drag-and-launch system to spawn planets, stars, or black holes live during runtime.
- **Smooth Dynamic Center-of-Mass Camera**: Automated tracking relative to total system barycenter with zoom controls.

---

## How to Play (Recommended)

To jump straight into the simulation without setting up a coding environment:
1. Navigate to the **[Releases](https://github.com/ChristosPng/space_simulation/releases)** section on the right side of this page.
2. Download the latest `.exe` file.
3. Double-click the downloaded file to launch the sandbox. No installation required!

## For Developers (Run from Source)

If you want to experiment with the code and run the simulation directly from your terminal:

## Prerequisites

Before running or compiling the simulation, ensure your system meets the following requirements:

1. **Python**: Version `3.8` or higher.
2. **Pygame**: Version `2.0` or higher (`pip install pygame`).
3. **C++ Compiler (`g++`)** *(Required only for compiling the native C++ acceleration library)*:
   - **Windows**: [MinGW-w64](https://www.mingw-w64.org/) or [MSYS2](https://www.msys2.org/) (ensure `g++` is added to system `PATH`).
   - **Linux**: Install via package manager (`sudo apt install build-essential g++`).
   - **macOS**: Install Xcode Command Line Tools (`xcode-select --install`).

---

## How to Run

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ChristosPng/space_simulation.git
   cd space_simulation
2. **Install Dependencies**
   ```bash
   pip install pygame
3. **Launch the simulation**
   ```bash
   python main.py

## Controls 

| Input | Action |
| :--- | :--- |
| **Right-Click + Drag** | Aim velocity vector and launch selected celestial body |
| **T** | Toggle spawn body type (*Planet* $\rightarrow$ *Star* $\rightarrow$ *BlackHole*) |
| **`[` / `]`** | Decrease / Increase spawn body mass |
| **`-` / `=`** | Decrease / Increase spawn body radius |
| **Spacebar** | Pause / Resume physics simulation |
| **Up / Down Arrows** | Increase / Decrease time step ($\Delta t$) |
| **Mouse Wheel** | Zoom in / Zoom out |
| **F11 / F** | Toggle Fullscreen mode |
| **Left Mouse Button and drag**| For free moving camera |
| **C** | Camera Lock |

---

## Native C++ Acceleration Performance

The physics loop supports dual execution. When compiled native libraries are present, `native_physics.py` automatically offloads calculation loops to C++:

| Body Count ($N$) | Python (`ms/frame`) | C++ Native (`ms/frame`) | Speedup |
| :--- | :--- | :--- | :--- |
| **25** | ~1.5 ms | ~0.02 ms | **~75x** |
| **100** | ~24.0 ms | ~0.25 ms | **~96x** |
| **400** | ~380.0 ms | ~3.80 ms | **~100x** |

To run the comparative benchmark suite locally:
```bash
python bench.py
