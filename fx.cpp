//fx.cpp - black hole --used for accretion disk + spacetime warp
// --more realistic stars

#include <cmath>
#include <cstdint>
#include <algorithm>

#ifdef _WIN32
    #define EXPORT extern "C" __declspec(dllexport)
#else
    #define EXPORT extern "C" __attribute__((visibility("default")))
#endif

namespace {

const float PI = 3.14159265358979f;

inline float clampf(float v, float a, float b) { return v < a ? a : (v > b ? b : v); }
inline float lerpf(float a, float b, float t) { return a + (b - a) * t; }
inline float smoothstep(float a, float b, float x) {
    float t = clampf((x - a) / (b - a), 0.0f, 1.0f);
    return t * t * (3.0f - 2.0f * t);
}
inline int wrap(int v, int p) { v %= p; return v < 0 ? v + p : v; }

struct Noise {
    int p[256];
    explicit Noise(uint32_t seed) {
        for (int i = 0; i < 256; ++i) p[i] = i;
        uint32_t s = seed * 2654435761u + 12345u;
        for (int i = 255; i > 0; --i) {
            s ^= s << 13; s ^= s >> 17; s ^= s << 5;
            std::swap(p[i], p[s % (i + 1)]);
        }
    }
    static float fade(float t) { return t * t * t * (t * (t * 6 - 15) + 10); }
    static float grad(int h, float x, float y) {
        int k = h & 7;
        float u = k < 4 ? x : y, v = k < 4 ? y : x;
        return ((k & 1) ? -u : u) + ((k & 2) ? -v : v);
    }
    float at(float x, float y, int period) const {     // repeats every `period` cells
        int x0 = (int)std::floor(x), y0 = (int)std::floor(y);
        float fx = x - x0, fy = y - y0;
        int xa = wrap(x0, period) & 255, xb = wrap(x0 + 1, period) & 255;
        int ya = wrap(y0, period) & 255, yb = wrap(y0 + 1, period) & 255;
        float u = fade(fx), v = fade(fy);
        int h00 = p[(p[xa] + ya) & 255], h10 = p[(p[xb] + ya) & 255];
        int h01 = p[(p[xa] + yb) & 255], h11 = p[(p[xb] + yb) & 255];
        return lerpf(lerpf(grad(h00, fx, fy), grad(h10, fx - 1, fy), u),
                     lerpf(grad(h01, fx, fy - 1), grad(h11, fx - 1, fy - 1), u), v);
    }
};

inline float tex(const uint8_t* t, int s, float u, float v) {
    u -= std::floor(u); v -= std::floor(v);
    float fx = u * s, fy = v * s;
    int x0 = (int)fx, y0 = (int)fy;
    if (x0 >= s) x0 = s - 1;
    if (y0 >= s) y0 = s - 1;
    float ax = fx - x0, ay = fy - y0;
    int x1 = x0 + 1 >= s ? 0 : x0 + 1, y1 = y0 + 1 >= s ? 0 : y0 + 1;
    float a = lerpf(t[y0 * s + x0], t[y0 * s + x1], ax);
    float b = lerpf(t[y1 * s + x0], t[y1 * s + x1], ax);
    return lerpf(a, b, ay) / 255.0f;
}

inline float fast_atan2(float y, float x) {
    float ax = std::fabs(x), ay = std::fabs(y);
    float mx = std::max(ax, ay), mn = std::min(ax, ay);
    if (mx == 0.0f) return 0.0f;
    float a = mn / mx, s = a * a;
    float r = ((-0.0464964749f * s + 0.15931422f) * s - 0.327622764f) * s * a + a;
    if (ay > ax) r = 1.57079637f - r;
    if (x < 0) r = 3.14159274f - r;
    if (y < 0) r = -r;
    return r;
}

struct CoronaLut {
    static const int N = 1024;
    static constexpr float HMAX = 4.0f;
    float bloom[N], whiten[N];
    CoronaLut() {
        for (int i = 0; i < N; ++i) {
            float h = i * (HMAX / (N - 1));
            bloom[i] = 0.85f * std::exp(-h / 0.11f) + 0.40f * std::exp(-h / 0.45f) + 0.16f * std::exp(-h / 1.1f);
            whiten[i] = std::exp(-h / 0.22f);
        }
    }
    int idx(float h) const { int i = (int)(h * ((N - 1) / HMAX)); return i < 0 ? 0 : (i > N - 1 ? N - 1 : i); }
};
const CoronaLut g_corona;

struct Acc {
    float r = 0, g = 0, b = 0, a = 0;
    void over(float sr, float sg, float sb, float sa) {
        float k = 1.0f - sa;
        r = sr * sa + r * k; g = sg * sa + g * k; b = sb * sa + b * k; a = sa + a * k;
    }
};

// glowing-metal colour ramp, t = 0..1
void heat(float t, float* c) {
    static const float S[5][3] = {{60, 8, 0}, {190, 55, 8}, {255, 125, 25}, {255, 205, 105}, {255, 250, 230}};
    t = clampf(t, 0.0f, 1.0f) * 4.0f;
    int i = (int)t; if (i > 3) i = 3;
    float f = t - i;
    for (int k = 0; k < 3; ++k) c[k] = lerpf(S[i][k], S[i + 1][k], f);
}

const float R_IN = 1.18f, R_OUT = 3.0f; 


bool disk_color(const uint8_t* noise, int ts, float t, float doppler, float r, float phi, float* rgb, float* alpha) {
    if (r < R_IN || r > R_OUT) return false;
    float tr = (r - R_IN) / (R_OUT - R_IN);
    float edge = smoothstep(0.0f, 0.06f, tr) * (1.0f - smoothstep(0.72f, 1.0f, tr));
    float omega = 1.7f / (r * std::sqrt(r));                     // inner gas orbits faster: the streaks wind up
    float u = (phi + omega * t) / (2 * PI) * 2.0f, v = tr * 1.2f + 0.13f;
    float n = 0.65f * tex(noise, ts, u, v) + 0.35f * tex(noise, ts, u * 2.0f + 0.37f, v * 2.3f);
    float nf = 0.35f + 1.25f * n;
    float q = 1.0f - tr;
    float base = 0.30f + 1.55f * q * std::sqrt(std::sqrt(q));       // q^1.25
    float bm = clampf(1.0f + doppler * std::cos(phi) / std::sqrt(r), 0.30f, 2.4f);   // one side brighter
    float I = base * nf * bm;
    heat(I / 2.1f, rgb);
    *alpha = edge * clampf(0.25f + 0.85f * I, 0.0f, 1.0f);
    return true;
}

} // namespace

EXPORT void fx_make_noise(int seed, int size, int base_period, int octaves, uint8_t* out) {
    if (size < 4 || base_period < 1 || octaves < 1 || !out) return;
    Noise n((uint32_t)seed);
    for (int y = 0; y < size; ++y)
        for (int x = 0; x < size; ++x) {
            float u = (float)x / size, v = (float)y / size;
            float sum = 0, amp = 1, norm = 0;
            int per = base_period;
            for (int o = 0; o < octaves; ++o) {
                sum += amp * n.at(u * per, v * per, per);
                norm += amp; amp *= 0.5f; per *= 2;
            }
            float val = 0.5f + 0.5f * (sum / norm) * 1.7f;
            out[y * size + x] = (uint8_t)(clampf(val, 0.0f, 1.0f) * 255.0f);
        }
}

EXPORT void fx_black_hole(const uint8_t* noise, int ts, int size, double span, double t,
                          double cos_i, double einstein, double doppler, uint8_t* out)
{
    if (!noise || !out || size < 4 || cos_i <= 0.02) return;
    const float c = size / 2.0f, k = (float)span / c;

    for (int py = 0; py < size; ++py) {
        for (int px = 0; px < size; ++px) {
            float X = (px + 0.5f - c) * k, Y = (py + 0.5f - c) * k;       // in black-hole radii
            float th = std::sqrt(X * X + Y * Y);
            uint8_t* o0 = &out[4 * ((size_t)py * size + px)];
            
            if (th >= (float)span) { o0[0] = o0[1] = o0[2] = o0[3] = 0; continue; }
            Acc acc;

            // ONLY draw the black shadow (Event Horizon)
            float sh = 1.0f - smoothstep(0.99f, 1.01f, th);
            if (sh > 0) acc.over(0, 0, 0, sh);

            uint8_t* o = &out[4 * ((size_t)py * size + px)];
            if (acc.a > 0.002f) {
                o[0] = (uint8_t)clampf(acc.r / acc.a, 0.0f, 255.0f);
                o[1] = (uint8_t)clampf(acc.g / acc.a, 0.0f, 255.0f);
                o[2] = (uint8_t)clampf(acc.b / acc.a, 0.0f, 255.0f);
                o[3] = (uint8_t)(clampf(acc.a, 0.0f, 1.0f) * 255.0f);
            } else {
                o[0] = o[1] = o[2] = o[3] = 0;
            }
        }
    }
}

EXPORT void fx_lens(const uint8_t* src, uint8_t* dst, int w, int h, double cx, double cy,
                    double einstein_px, double shadow_px, double region_px)
{
    if (!src || !dst || w < 2 || h < 2) return;
    const float fcx = (float)cx, fcy = (float)cy, E2 = (float)(einstein_px * einstein_px);
    const float R = (float)region_px, shadow = (float)shadow_px;

    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            uint8_t* o = &dst[3 * ((size_t)y * w + x)];
            float dx = x + 0.5f - fcx, dy = y + 0.5f - fcy;
            float th = std::sqrt(dx * dx + dy * dy);
            if (th >= R || th < 1e-3f) {
                const uint8_t* s = &src[3 * ((size_t)y * w + x)];
                o[0] = s[0]; o[1] = s[1]; o[2] = s[2];
                continue;
            }
            float fade = smoothstep(R, R * 0.55f, th);
            float beta = th - E2 / th * fade;
            float sx = fcx + dx / th * beta - 0.5f, sy = fcy + dy / th * beta - 0.5f;
            sx = clampf(sx, 0.0f, (float)(w - 1) - 0.001f);
            sy = clampf(sy, 0.0f, (float)(h - 1) - 0.001f);
            int x0 = (int)sx, y0 = (int)sy;
            float ax = sx - x0, ay = sy - y0;
            const uint8_t* p00 = &src[3 * ((size_t)y0 * w + x0)];
            const uint8_t* p10 = p00 + 3;
            const uint8_t* p01 = p00 + 3 * (size_t)w;
            const uint8_t* p11 = p01 + 3;
            float dark = th < shadow ? 0.0f : 1.0f;
            for (int ch = 0; ch < 3; ++ch) {
                float v = lerpf(lerpf(p00[ch], p10[ch], ax), lerpf(p01[ch], p11[ch], ax), ay);
                o[ch] = (uint8_t)clampf(v * dark, 0.0f, 255.0f);
            }
        }
    }
}

EXPORT void fx_star(const uint8_t* noise, int ts, int size, double span, double spin, double t,
                    double cr, double cg, double cb, double phase, uint8_t* out)
{
    if (!noise || !out || size < 4) return;
    const float c = size / 2.0f, k = (float)span / c;
    const float fspan = (float)span, ft = (float)t, fph = (float)phase;
    const float cs = std::cos((float)spin), sn = std::sin((float)spin);
    const float a2 = ft * 0.35f, cs2 = std::cos(a2), sn2 = std::sin(a2);
    const float edge_px = c / fspan;                        // pixels per star radius

    for (int py = 0; py < size; ++py) {
        for (int px = 0; px < size; ++px) {
            float X = (px + 0.5f - c) * k, Y = (py + 0.5f - c) * k;
            float rho = std::sqrt(X * X + Y * Y);
            if (rho >= fspan) { uint8_t* o1 = &out[4 * ((size_t)py * size + px)]; o1[0] = o1[1] = o1[2] = o1[3] = 0; continue; }
            Acc acc;

            if (rho > 0.97f) {
                float h = std::max(rho - 1.0f, 0.0f);
                float ang = fast_atan2(Y, X) / (2 * PI) + (float)spin / (2 * PI) * 0.4f + fph;
                float rays = tex(noise, ts, ang * 3.0f, h * 0.07f + 0.1f + ft * 0.002f);    // slow in h -> long streaks
                float rays2 = tex(noise, ts, ang * 7.0f + 0.3f, h * 0.10f + 0.6f);
                float streak_f = 0.35f + 1.1f * (0.65f * rays + 0.35f * rays2);
                int li = g_corona.idx(h);
                float I = g_corona.bloom[li] * streak_f;
                if (h < 0.4f) {                                  // only near the surface: the thin rim and the flares
                    if (h < 0.25f)
                        I += 0.9f * std::exp(-h / 0.025f) * (0.8f + 0.5f * tex(noise, ts, ang * 6.0f + ft * 0.05f, 0.77f));
                    float angf = ang - std::floor(ang), fl = 0.0f;
                    for (int i = 0; i < 3; ++i) {                // prominences: bright loops near the limb
                        float ai = std::fmod(0.13f + 0.31f * i + 0.004f * ft + fph * 0.7f, 1.0f);
                        float da = std::fabs(angf - ai);
                        da = std::min(da, 1.0f - da);
                        if (da > 0.06f) continue;
                        float pulse = 0.6f + 0.4f * std::sin(ft * 0.9f + i * 2.1f + fph * 6.0f);
                        float qa = da / 0.016f, qh = (h - 0.11f) / 0.06f;
                        fl += pulse * std::exp(-(qa * qa) - (qh * qh));
                    }
                    I += fl * 1.3f;
                }
                I *= (1.0f - smoothstep(fspan * 0.62f, fspan, rho));
                float whiten = g_corona.whiten[li];                                         // white-hot at the limb
                acc.over(lerpf((float)cr, 255.0f, whiten), lerpf((float)cg, 250.0f, whiten), lerpf((float)cb, 240.0f, whiten),
                         clampf(I, 0.0f, 1.0f));
            }

            float edge = clampf((1.0f - rho) * edge_px + 0.5f, 0.0f, 1.0f);
            if (edge > 0.0f) {
                float nz = std::sqrt(std::max(0.0f, 1.0f - rho * rho));
                float limb = 0.42f + 0.58f * std::sqrt(nz);                      // darker toward the edge
                float xr = cs * X + sn * Y, yr = -sn * X + cs * Y;                    // the star's spin
                float xq = cs2 * X - sn2 * Y, yq = sn2 * X + cs2 * Y;                 // a second layer drifting the other way
                float g1 = tex(noise, ts, xr * 1.1f + 0.5f + fph, yr * 1.1f + 0.5f);
                float g2 = tex(noise, ts, xq * 2.0f + 0.21f, yq * 2.0f + 0.77f + fph);
                float gran = 0.5f * g1 + 0.5f * g2;
                gran = clampf((gran - 0.5f) * 1.7f + 0.5f, 0.0f, 1.0f);              // more contrast: bright cells, dark lanes
                float sp = tex(noise, ts, xr * 0.55f + 0.31f + fph, yr * 0.55f + 0.62f);
                float spot = smoothstep(0.67f, 0.76f, sp);                            // small sunspots
                float bright = limb * (0.55f + 0.95f * gran) * (1.0f - 0.5f * spot * (0.5f + 0.5f * nz));
                float hot = 0.30f * nz * nz * nz;                                     // whiter in the middle
                acc.over(clampf(lerpf((float)cr, 255.0f, hot) * bright, 0.0f, 255.0f),
                         clampf(lerpf((float)cg, 255.0f, hot) * bright, 0.0f, 255.0f),
                         clampf(lerpf((float)cb, 255.0f, hot) * bright, 0.0f, 255.0f), edge);
            }

            uint8_t* o = &out[4 * ((size_t)py * size + px)];
            if (acc.a > 0.002f) {
                o[0] = (uint8_t)clampf(acc.r / acc.a, 0.0f, 255.0f);
                o[1] = (uint8_t)clampf(acc.g / acc.a, 0.0f, 255.0f);
                o[2] = (uint8_t)clampf(acc.b / acc.a, 0.0f, 255.0f);
                o[3] = (uint8_t)(clampf(acc.a, 0.0f, 1.0f) * 255.0f);
            } else {
                o[0] = o[1] = o[2] = o[3] = 0;
            }
        }
    }
}