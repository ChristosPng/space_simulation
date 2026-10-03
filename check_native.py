from helper import Helper
import native_physics

class B:
    def __init__(s, x, y, vx, vy, m):
        s.position = [x,y]; s.velocity = [vx, vy]; s.mass = m

def make():
    return [B(0, 0, 0, 0, 100000), B(800, 0, 0, 3.5, 1000), B(840, 0, 0, 5, 5)]

a,b = make(), make()
for _ in range(100):
    for _ in range(4):
        Helper.rk4_step(a, 0.5) # python
    native_physics.step(b, 2.0, 4) #c++

diff = max(abs(p - q) for x, y in zip(a,b)
            for p, q in zip(x.position + x.velocity, y.position + y.velocity))
print("available:", native_physics.available, "max diff", diff)