//code for making rk4 calculations in c++ for improved speed at high body counts

#include <cmath>
#include <vector>

#ifdef _WIN32
    #define EXPORT extern "C" __declspec(dllexport)
#else
    #define EXPORT extern "C" __attribute__((visibility("default")))
#endif

static void accelerations(int n, const double* pos, const double* mass, double G, double soft, double* acc)
{
    for (int k = 0; k < 2*n; ++k) acc[k] = 0.0;

    for (int i = 0; i < n ; ++i)
    {
        for (int j = i + 1; j < n; ++j)
        {
            double dx = pos[2*j] - pos[2*i];
            double dy = pos[2*j + 1] - pos[2*i + 1];
            double d2 = dx * dx + dy * dy + soft;
            double f = G / (d2 * std::sqrt(d2));

            acc[2*i] += f  * dx * mass[j];
            acc[2*i + 1] += f  * dy * mass[j];
            acc[2*j] -= f  * dx* mass[i];
            acc[2*j + 1] -= f  * dy * mass[i];
        }
    }
}

EXPORT void rk4_steps(int n, double* pos, double* vel, const double* mass, double h, int steps, double G, double soft)
{
    if (n <= 0 || steps <= 0 || !pos || !vel || !mass) return;

    const int m = 2 * n;

    std::vector<double> a1(m), a2(m), a3(m), a4(m);
    std::vector<double> v2(m), v3(m), v4(m), tp(m);

    for (int s = 0; s < steps; ++s){
        accelerations(n, pos, mass, G, soft, a1.data());

        for (int k = 0; k < m; ++k){
            tp[k] = pos[k] + vel[k] * h / 2;
            v2[k] = vel[k] + a1[k] * h / 2;
        }
        accelerations(n, tp.data(), mass, G, soft, a2.data());

        for (int k = 0; k < m; ++k) {
            tp[k] = pos[k] + v2[k] * h / 2;
            v3[k] = vel[k] + a2[k] * h / 2;
        }
        accelerations(n, tp.data(), mass, G, soft, a3.data());

        for (int k = 0; k < m; ++k) {
            tp[k] = pos[k] + v3[k] * h;
            v4[k] = vel[k] + a3[k] * h;
        }
        accelerations(n, tp.data(), mass, G, soft, a4.data());

        for (int k = 0; k < m; ++k) {
            pos[k] += (h / 6) * (vel[k] + 2*v2[k] + 2*v3[k] + v4[k]);   // uses OLD vel
            vel[k] += (h / 6) * (a1[k] + 2*a2[k] + 2*a3[k] + a4[k]);
        }
    }
}