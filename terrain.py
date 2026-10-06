"""terrain.py - flat (2D) procedural planet surfaces, computed by terrain.dll (C++).

Each planet gets a noise texture baked once; every frame it is drawn as a lit disc that spins
in place (like looking straight down on the planet's pole).
If the library is missing, `available` is False and planets stay plain circles.
"""
import ctypes
import math
import os
import random
import sys
import zlib

import pygame

MIN_RADIUS_PX = 6          
MAX_RADIUS_PX = 600      
MAX_RENDER = 160          
MAX_RENDERS_PER_FRAME = 6  
MAX_BAKES_PER_FRAME = 1    
GAS_RADIUS = 18           
LIGHT_Z = 0.0           


if getattr(sys, "frozen", False):      
    _BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

_LIB_NAME = {"win32": "terrain.dll", "darwin": "libterrain.dylib"}.get(sys.platform, "libterrain.so")


def _load():
    path = os.path.join(_BASE_DIR, _LIB_NAME)
    if not os.path.exists(path):
        print(f"[terrain] {_LIB_NAME} not found - planets stay flat")
        return None
    try:
        lib = ctypes.CDLL(path)
    except OSError as e:
        print(f"[terrain] could not load {_LIB_NAME}: {e}")
        return None

    u8p = ctypes.POINTER(ctypes.c_uint8)
    dp = ctypes.POINTER(ctypes.c_double)
    
    lib.terrain_generate.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_double,
                                     ctypes.c_int, dp, ctypes.c_int, u8p]
    lib.terrain_generate.restype = None
    lib.terrain_render.argtypes = [u8p, ctypes.c_int, ctypes.c_int, ctypes.c_double,
                                   ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, u8p]
    lib.terrain_render.restype = None
    return lib


_lib = _load()
available = _lib is not None


_renders = 0
_bakes = 0


def begin_frame():
    """Call once per frame, before drawing the planets."""
    global _renders, _bakes
    _renders = 0
    _bakes = 0


_WHITE = (255, 255, 255)


def _mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def _mul(a, k):
    return tuple(min(255.0, c * k) for c in a)


def _palette(kind, c):
    c = tuple(float(v) for v in c[:3])
    if kind == "earthlike":      # ocean in the planet's colour + contrasting land
        return [(0.00, _mul(c, .30)), (0.34, _mul(c, .65)), (0.47, _mix(c, _WHITE, .30)),
                (0.50, (196, 180, 130)), (0.58, (72, 132, 62)), (0.76, (112, 100, 72)),
                (0.92, (236, 236, 242)), (1.00, _WHITE)]
    if kind == "desert":         # shades of the planet's colour
        return [(0.00, _mul(c, .50)), (0.35, _mul(c, .75)), (0.62, c),
                (0.85, _mix(c, _WHITE, .28)), (1.00, _mix(c, _WHITE, .50))]
    return [(0.00, _mul(c, .55)), (0.30, _mul(c, .85)), (0.50, c),      # "banded"
            (0.72, _mix(c, _WHITE, .33)), (1.00, _mix(c, _WHITE, .60))]


class PlanetSurface:
    """One planet's look. The seed comes from its NAME, so the same planet always looks the same
    (and a merged planet, which keeps the heavier parent's name, keeps that parent's terrain)."""

    def __init__(self, name, color, radius):
        self.seed = zlib.crc32(str(name).encode("utf-8")) & 0x7FFFFFFF
        rnd = random.Random(self.seed)
        self.color = color
        r, g, b = color[0], color[1], color[2]

        if radius >= GAS_RADIUS:
            self.kind, self.style = "banded", 1
            self.freq, self.octaves = rnd.uniform(18.0, 36.0), 4
            self.atmo = 0.5
        elif b > r and b > g:
            self.kind, self.style = "earthlike", 0
            self.freq, self.octaves = rnd.uniform(2.0, 3.2), 6
            self.atmo = 0.9
        else:
            self.kind, self.style = "desert", 0
            self.freq, self.octaves = rnd.uniform(2.4, 3.8), 5
            self.atmo = 0.15

        self.tsize = 256 if radius >= 12 else 128
        self.spin_mult = rnd.uniform(0.6, 1.6) * rnd.choice((1, 1, 1, -1))   # some spin backwards
        self.rgba = None

    def ready(self):
        """True once the texture exists. Baking is limited to a few per frame."""
        global _bakes
        if self.rgba is not None:
            return True
        if _bakes >= MAX_BAKES_PER_FRAME:
            return False
        _bakes += 1
        flat = [v for pos, rgb in _palette(self.kind, self.color) for v in (pos, *rgb)]
        stops = (ctypes.c_double * len(flat))(*flat)
        rgba = (ctypes.c_uint8 * (self.tsize * self.tsize * 4))()
        _lib.terrain_generate(self.seed, self.tsize, self.style, self.freq, self.octaves,
                              stops, len(flat) // 4, rgba)
        self.rgba = rgba
        return True

    def sprite(self, size, spin_deg, light):
        out = (ctypes.c_uint8 * (size * size * 4))()
        _lib.terrain_render(self.rgba, self.tsize, size, math.radians(spin_deg) * self.spin_mult,
                            light[0], light[1], light[2], self.atmo, out)
        return pygame.image.frombuffer(bytes(out), (size, size), "RGBA").convert_alpha()


def draw_planet(screen, planet, sx, sy, sr, star):
    
    global _renders
    if not available or sr < MIN_RADIUS_PX or sr > MAX_RADIUS_PX:
        return False
    if sx < -sr or sy < -sr or sx > screen.get_width() + sr or sy > screen.get_height() + sr:
        return True                                   
    if _renders >= MAX_RENDERS_PER_FRAME:
        return False

    surf = planet.surface
    if surf is None:
        surf = planet.surface = PlanetSurface(planet.name, planet.color, planet.radius)
    if not surf.ready():
        return False

    if star is not None:                                   # light comes from the nearest star
        dx = star.position[0] - planet.position[0]
        dy = star.position[1] - planet.position[1]
        d = math.hypot(dx, dy) or 1.0
        light = (dx / d, dy / d, LIGHT_Z)
    else:
        light = (0.0, 0.0, 1.0)                            # no star: light the whole face

    diameter = sr * 2
    render_size = min(MAX_RENDER, ((diameter + 15) // 16) * 16)   # few distinct sizes
    img = surf.sprite(render_size, planet.visual_angle, light)
    if render_size != diameter:
        img = pygame.transform.smoothscale(img, (diameter, diameter))
    screen.blit(img, (int(sx) - sr, int(sy) - sr))
    _renders += 1
    return True