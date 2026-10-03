"""loads physics.dll

if the library fails to load it will fall back to the python implemenetantion
""" 

import ctypes
import os
import sys

from helper import G, SOFTENING

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_LIB_NAME = {"win32": "physics.dll", "darwin": "libphysics.dylib"}.get(sys.platform, "libphysics.so")


def _load():
    path = os.path.join(_BASE_DIR, _LIB_NAME)
    if not os.path.exists(path):
        print(f"[native_physics] {_LIB_NAME} not found, using pure Python Physics")
        return None
    try: 
        lib = ctypes.CDLL(path)
    except OSError as e:
        print(f"[native physics] cound not load {_LIB_NAME}: {e}")
        return None

    dp = ctypes.POINTER(ctypes.c_double)

    lib.rk4_steps.argtypes = [
        ctypes.c_int,  #n  
        dp, dp, dp,     #pos, vel, mass
        ctypes.c_double,  #h
        ctypes.c_int,      #steps
        ctypes.c_double,  #G
        ctypes.c_double,  #soft
    ]

    lib.rk4_steps.restype = None
    return lib

_lib = _load()
available = _lib is not None

def step(bodies, total_dt, steps):
    """True if the native library did the work else false if Python fallback should b used"""
    if _lib is None or not bodies:
        return False

    n = len(bodies)
    pos = (ctypes.c_double * (2 * n))(*[c for b in bodies for c in b.position])
    vel = (ctypes.c_double * (2 * n))(*[c for b in bodies for c in b.velocity])
    mass = (ctypes.c_double * n)(*[b.mass for b in bodies])

    _lib.rk4_steps(n, pos, vel, mass, total_dt / steps, steps, G, SOFTENING)

    for i, b in enumerate(bodies):
        b.position[0] = pos[2 * i]
        b.position[1] = pos[2 * i + 1]
        b.velocity[0] = vel[2 * i]
        b.velocity[1] = vel[2 * i + 1]
    return True
