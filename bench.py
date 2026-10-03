import time, random, math
from helper import Helper
import native_physics

class Body:
    def __init__(self, x, y, vx, vy, m):
        self.position = [x,y]
        self.velocity = [vx, vy]
        self.mass = m

def make_bodies(n, seed=1):
    rnd = random.Random(seed)
    bodies = [Body(0, 0, 0, 0, 100000)]
    for _ in range(n - 1):
        r = rnd.uniform(300, 2000)
        a = rnd.uniform(0, 2* math.pi)
        v = math.sqrt(0.1 * 100000 / r)
        bodies.append(Body(r * math.cos(a), r * math.sin(a), 
                        -v* math.sin(a), v * math.cos(a), rnd.uniform(5, 3000)))
    return bodies

print("native library loaded:", native_physics.available)

a, b = make_bodies(8), make_bodies(8)
for _ in range(200):
    for _ in range (4):
        Helper.rk4_step(a, 2.0 / 4)
    native_physics.step(a, 2.0, 4)
maxdiff = max(abs(p - q) for x, y in zip(a, b)
              for p, q in zip(x.position + x.velocity, y.position + y.velocity))
print(f"max |python - c++| after 800 RK4 steps: {maxdiff:.3e}")

print(f"\n{'bodies':>7} {'python ms/frame':>16} {'c++ ms/frame':>13} {'speedup':>8}")
for n in (6, 25, 50, 100, 200, 400):
    reps = 3 if n <= 100 else 1
    bp = make_bodies(n)
    t = time.perf_counter()
    for _ in range(reps):
        for _ in range(16):
            Helper.rk4_step(bp, 8.0 / 16)
    py_ms = (time.perf_counter() - t) / reps * 1000

    bc = make_bodies(n)
    t = time.perf_counter()
    for _ in range(reps * 5):
        native_physics.step(bc, 8.0, 16)
    cpp_ms = (time.perf_counter() - t) / (reps * 5) * 1000
    print(f"{n:>7} {py_ms:>16.2f} {cpp_ms:>13.3f} {py_ms / cpp_ms:>7.0f}x")