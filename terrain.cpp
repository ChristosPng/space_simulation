//terrain.cpp - planet surface

#include <cmath>
#include <cstdint>
#include <vector>
#include <map>
#include <algorithm>

#ifdef _WIN32
    #define EXPORT extern "C" __declspec(dllexport)
#else
    #define EXPORT extern "C" __attribute__((visibility("default")))
#endif

namespace{
    
    const double PI = 3.14159265358979323846;
    const float SLOPE_SCALE = 30.0f;


// Perlin Noise impl
struct Noise {
    int p[512];

    explicit Noise(uint32_t seed){
        int perm[256];
        for (int i = 0; i < 256; ++i) perm[i] = i;
        uint32_t s = seed * 2654435761u + 12345u;
        for (int i = 255; i > 0; --i){      //shuffle with a small xor gen
            s ^= s << 13; s ^= s >> 17; s ^= s << 5;
            std::swap(perm[i], perm[s % (i + 1)]);
        }
        for (int i=0; i < 512; ++i) p[i] = perm[i & 255];
    }

    static double fade(double t) {return t * t * t *(t * (t * 6 - 15) + 10);}
    static double lerp(double t, double a, double b) { return a + t * (b - a); }
    static double grad(int h, double x, double y) {
        int k = h & 7;
        double u = k < 4 ? x : y, v = k < 4 ? y : x;
        return ((k & 1) ? -u : u) + ((k & 2) ? -v : v);
    }

    double at(double x, double y) const {
        double fx = std::floor(x), fy = std::floor(y);
        int X = (int)fx & 255, Y = (int)fy & 255;    
        x -= fx, y -= fy;
        double u = fade(x), v = fade(y);
        int A = p[X] + Y, B = p[X + 1] + Y;
        return lerp(v, lerp(u, grad(p[A], x, y),     grad(p[B], x - 1, y)),
                       lerp(u, grad(p[A + 1], x, y - 1), grad(p[B + 1], x - 1, y - 1)));
    }

    //several layers of noise, each half as strong and twice as detailed
    double fbm(double x, double y, int octaves) const {
        double sum = 0, amp = 1, norm = 0;
        for (int o = 0; o < octaves; ++o){
            sum += amp * at(x,y);
            norm += amp; amp *= 0.5; x *=2; y*=2;
        }
        return sum / norm;
    }
};

void palette_color(const double* stops, int n, double t, uint8_t* rgb){
    t = std::max(0.0, std::min(1.0, t));
    int i = 0;
    while(i < n - 2 && t > stops[4 * (i + 1)]) ++i;
    double t0 = stops[4 * i], t1 = stops[4 * (i + 1)];
    double f = t1 > t0 ? (t - t0) / (t1 - t0) : 0.0;
    f = std::max(0.0, std::min(1.0, f));
    for (int c = 0; c < 3; ++c) {
        double v = stops[4 * i + 1 + c] + f * (stops[4 * (i + 1) + 1 + c] - stops[4 * i + 1 + c]);
        rgb[c] = (uint8_t)std::max(0.0, std::min(255.0, v));
    }
}

}

EXPORT void terrain_generate(int seed, int size, int style, double freq, int octaves,
                             const double* stops, int n_stops, uint8_t* out_rgba)
{
    if (size < 2 || n_stops < 2 || !stops || !out_rgba) return;
    Noise noise((uint32_t)seed);
    Noise warp((uint32_t)seed + 7919u);

    for (int y = 0; y < size; ++y) {
        double ny = (double)y / (size - 1) * 2 - 1;
        for (int x = 0; x < size; ++x) {
            double nx = (double)x / (size - 1) * 2 - 1;
            double value;
            if (style == 1) {
                double r = std::sqrt(nx * nx + ny * ny);
                double turb = warp.fbm(nx * 1.5 + 10, ny * 1.5 + 10, 4);
                double detail = noise.fbm(nx * 4 + 20, ny * 4 + 20, octaves);
                value = 0.5 + 0.38 * std::sin(r * freq + turb * 3.2) + 0.30 * detail;
            } else {
                value = 0.5 + 1.25 * noise.fbm(nx * freq + 30, ny * freq + 30, octaves);
            }
            palette_color(stops, n_stops, value, &out_rgba[4 * ((size_t)y * size + x)]);
            out_rgba[4 * ((size_t)y * size + x) + 3] = 255;
        }
    }
}

EXPORT void terrain_render(const uint8_t* rgba, int tsize, int size, double spin,
                           double lx, double ly, double lz, double atmo, uint8_t* out)
{
    if (!rgba || !out || tsize < 2 || size < 2) return;
    double ll = std::sqrt(lx * lx + ly * ly + lz * lz);
    if (ll < 1e-9) { lx = 0; ly = 0; lz = 1; ll = 1; }
    const float flx = (float)(lx / ll), fly = (float)(ly / ll), flz = (float)(lz / ll);
    const float cs = (float)std::cos(spin), sn = (float)std::sin(spin);
    const float R = size / 2.0f;
    const float last = (float)(tsize - 1);

    for (int py = 0; py < size; ++py) {
        for (int px = 0; px < size; ++px) {
            uint8_t* o = &out[4 * ((size_t)py * size + px)];
            float nx = (px + 0.5f - R) / R, ny = (py + 0.5f - R) / R;     // -1..1 across the disc
            float r2 = nx * nx + ny * ny;
            float r = std::sqrt(r2);
            float a = std::max(0.0f, std::min(1.0f, (1.0f - r) * R));     // soft 1px edge
            if (a <= 0) { o[0] = o[1] = o[2] = o[3] = 0; continue; }

            float tx = cs * nx + sn * ny, ty = -sn * nx + cs * ny;
            float fu = std::max(0.0f, std::min(last - 0.001f, (tx * 0.5f + 0.5f) * last));
            float fv = std::max(0.0f, std::min(last - 0.001f, (ty * 0.5f + 0.5f) * last));
            int x0 = (int)fu, y0 = (int)fv;
            float ax = fu - x0, ay = fv - y0;
            size_t i00 = (size_t)y0 * tsize + x0, i10 = i00 + 1;
            size_t i01 = i00 + tsize, i11 = i01 + 1;
            float w00 = (1 - ax) * (1 - ay), w10 = ax * (1 - ay), w01 = (1 - ax) * ay, w11 = ax * ay;

            float nz = std::sqrt(std::max(0.0f, 1.0f - r2));
            float ndl = nx * flx + ny * fly + nz * flz;
            float t = (ndl + 0.04f) / 0.40f; t = std::max(0.0f, std::min(1.0f, t));
            float lit = t * t * (3 - 2 * t);                              // soft day/night line
            float shade = (0.07f + 0.93f * lit) * (0.80f + 0.20f * nz);   // + darker toward the rim
            float haze = (float)atmo * r2 * r2 * r2 * lit;                // thin glow at the rim

            for (int k = 0; k < 3; ++k) {
                float c = rgba[4 * i00 + k] * w00 + rgba[4 * i10 + k] * w10 + rgba[4 * i01 + k] * w01 + rgba[4 * i11 + k] * w11;
                c *= shade;
                c += (255.0f - c) * haze * 0.6f;
                o[k] = (uint8_t)std::max(0.0f, std::min(255.0f, c));
            }
            o[3] = (uint8_t)(a * 255.0f);
        }
    }
}