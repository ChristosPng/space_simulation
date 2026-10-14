"""fx.py - black holes (lensed accretion disk + spacetime warp) and stars (churning surface,
corona, flares), computed by fx.dll (C++).

If the library is missing, `available` is False and everything keeps its simple look.
"""
import ctypes
import math
import os
import sys
import zlib

import pygame

#tuning knobs
BUDGET_MS = 12.0           # estimated time per frame all effects together may use (lower it if you lose fps)
NS_STAR, NS_BH, NS_LENS = 70, 70, 30    # rough cost per pixel in nanoseconds

STAR_SPAN = 2.6            # a star sprite reaches this many star radii out (the corona)
MAX_STAR_SPRITE = 320      # draw at most this many pixels across, then scale up
MIN_STAR_RADIUS_PX = 3     # smaller than this on screen -> the simple look

BH_SPAN = 4.0              # a black hole sprite reaches this many black-hole radii out
BH_COS_I = 0.22            # tilt of the accretion disk: smaller = more edge-on
BH_EINSTEIN = 1.25         # how strongly the disk's light bends over the shadow (in radii)
BH_DOPPLER = 0.55          # 0 = even disk, bigger = one side much brighter
MAX_BH_SPRITE = 256
MIN_BH_RADIUS_PX = 3       # smaller than this on screen -> the simple look

LENS_ENABLED = True        # the spacetime warp of whatever is behind a black hole
LENS_EINSTEIN = 1.7        # warp strength (in radii)
LENS_REACH = 6.0           # the warp fades out this many radii from the hole
MAX_LENS_PX = 220          # biggest warp radius in pixels (bigger holes keep only the sprite)


if getattr(sys, "frozen", False):          # running as a PyInstaller exe
    _BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

_LIB_NAME = {"win32": "fx.dll", "darwin": "libfx.dylib"}.get(sys.platform, "libfx.so")
NOISE_SIZE = 256


def _load():
    path = os.path.join(_BASE_DIR, _LIB_NAME)
    if not os.path.exists(path):
        print(f"[fx] {_LIB_NAME} not found - simple stars and black holes")
        return None
    try:
        lib = ctypes.CDLL(path)
    except OSError as e:
        print(f"[fx] could not load {_LIB_NAME}: {e}")
        return None

    u8p = ctypes.POINTER(ctypes.c_uint8)
    c_int, c_dbl = ctypes.c_int, ctypes.c_double
    # IMPORTANT: always declare argtypes, otherwise ctypes mangles doubles and pointers
    lib.fx_make_noise.argtypes = [c_int, c_int, c_int, c_int, u8p]
    lib.fx_black_hole.argtypes = [u8p, c_int, c_int, c_dbl, c_dbl, c_dbl, c_dbl, c_dbl, u8p]
    lib.fx_lens.argtypes = [u8p, u8p, c_int, c_int, c_dbl, c_dbl, c_dbl, c_dbl, c_dbl]
    lib.fx_star.argtypes = [u8p, c_int, c_int, c_dbl, c_dbl, c_dbl, c_dbl, c_dbl, c_dbl, c_dbl, u8p]
    for f in (lib.fx_make_noise, lib.fx_black_hole, lib.fx_lens, lib.fx_star):
        f.restype = None
    return lib


_lib = _load()
available = _lib is not None

_noise = None
if available:                                   # one shared noise texture for every effect
    _noise = (ctypes.c_uint8 * (NOISE_SIZE * NOISE_SIZE))()
    _lib.fx_make_noise(1234, NOISE_SIZE, 8, 5, _noise)

_tobytes = getattr(pygame.image, "tobytes", None) or pygame.image.tostring   # name changed in newer pygame
_lens_ok = True

# per-frame budget 
_spent = 0.0


def begin_frame():
    """Call once per frame, before drawing the stars and black holes."""
    global _spent
    _spent = 0.0


def _fit(size, ns):
    """Shrink `size` until it fits in what is left of the frame budget. Returns 0 if nothing fits."""
    while size > 48 and _spent + size * size * ns / 1e6 > BUDGET_MS:
        size = int(size * 0.75)
    return size if _spent + size * size * ns / 1e6 <= BUDGET_MS else 0


def _offscreen(screen, sx, sy, reach):
    return sx < -reach or sy < -reach or sx > screen.get_width() + reach or sy > screen.get_height() + reach


def _blit_sprite(screen, out, size, full, sx, sy):
    img = pygame.image.frombuffer(bytes(out), (size, size), "RGBA").convert_alpha()
    if size != full:
        img = pygame.transform.smoothscale(img, (full, full))
    screen.blit(img, (int(sx) - full // 2, int(sy) - full // 2))


def draw_star(screen, star, sx, sy, zoom):
    """Draw a star with a churning surface, sunspots, corona and flares.
    Returns True if it drew the star (or it is off-screen), False if the caller should draw the simple look."""
    global _spent
    if not available:
        return False
    radius = star.radius * zoom
    if radius < MIN_STAR_RADIUS_PX:
        return False
    full = int(radius * STAR_SPAN * 2)
    if _offscreen(screen, sx, sy, full // 2):
        return True

    size = _fit(min(MAX_STAR_SPRITE, full), NS_STAR)
    if size == 0:
        return False

    phase = getattr(star, "_fx_phase", None)
    if phase is None:                                   # every star gets its own spots and flares
        phase = star._fx_phase = (zlib.crc32(str(star.name).encode("utf-8")) & 0xFFFF) / 65535.0
    r, g, b = star.color[0], star.color[1], star.color[2]

    out = (ctypes.c_uint8 * (size * size * 4))()
    _lib.fx_star(_noise, NOISE_SIZE, size, STAR_SPAN, math.radians(star.visual_angle), star.visual_t,
                 r, g, b, phase, out)
    _blit_sprite(screen, out, size, full, sx, sy)
    _spent += size * size * NS_STAR / 1e6
    return True


def _warp(screen, sx, sy, u, lens_r):
    """Bend whatever is already drawn around the black hole (the spacetime warp)."""
    global _spent, _lens_ok
    r = int(lens_r)
    x0, y0 = max(0, int(sx) - r), max(0, int(sy) - r)
    x1, y1 = min(screen.get_width(), int(sx) + r), min(screen.get_height(), int(sy) + r)
    w, h = x1 - x0, y1 - y0
    cost = w * h * NS_LENS / 1e6
    if w < 8 or h < 8 or _spent + cost > BUDGET_MS:
        return
    try:
        data = _tobytes(screen.subsurface(pygame.Rect(x0, y0, w, h)), "RGB")
        src = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
        dst = (ctypes.c_uint8 * len(data))()
        _lib.fx_lens(src, dst, w, h, sx - x0, sy - y0, LENS_EINSTEIN * u, u, lens_r)
        screen.blit(pygame.image.frombuffer(bytes(dst), (w, h), "RGB"), (x0, y0))
        _spent += cost
    except (pygame.error, ValueError) as e:
        print(f"[fx] spacetime warp disabled: {e}")
        _lens_ok = False


def draw_black_hole(screen, bh, sx, sy, zoom):
    """Draw a black hole: warped background, shadow, photon ring and a lensed accretion disk.
    Returns True if it drew it (or it is off-screen), False if the caller should draw the simple look."""
    global _spent
    if not available:
        return False
    u = bh.radius * zoom                      # one black-hole radius, in pixels
    if u < MIN_BH_RADIUS_PX:
        return False
    lens_r = min(LENS_REACH * u, MAX_LENS_PX)
    full = int(BH_SPAN * u * 2)
    if _offscreen(screen, sx, sy, max(full // 2, lens_r)):
        return True

    if LENS_ENABLED and _lens_ok and lens_r >= 3.2 * u:
        _warp(screen, sx, sy, u, lens_r)

    size = _fit(min(MAX_BH_SPRITE, full), NS_BH)
    if size == 0:
        return False
    out = (ctypes.c_uint8 * (size * size * 4))()
    _lib.fx_black_hole(_noise, NOISE_SIZE, size, BH_SPAN, bh.visual_t, BH_COS_I, BH_EINSTEIN, BH_DOPPLER, out)
    _blit_sprite(screen, out, size, full, sx, sy)
    _spent += size * size * NS_BH / 1e6
    return True