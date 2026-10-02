import math
import random
import pygame

BOUNDARY_MARGIN = 200
G = 0.1
SOFTENING = 200

class Helper:

    @staticmethod
    def get_accelerations(positions, masses):
        accels = [[0,0] for _ in range(len(positions))]

        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                dx = positions[j][0] - positions[i][0]
                dy = positions[j][1] - positions[i][1]
                dist_sq = dx**2 + dy**2 + SOFTENING
                dist = math.sqrt(dist_sq)

                if dist == 0:
                    continue

                force_mag = G / (dist_sq * dist) 
                
                accels[i][0] += force_mag * dx * masses[j]
                accels[i][1] += force_mag * dy * masses[j]
                
                accels[j][0] -= force_mag * dx * masses[i]
                accels[j][1] -= force_mag * dy * masses[i]
        return accels

    @staticmethod
    def calculate_gravitational_force(body1, body2):
        G = 0.1
        softening = 200
        distance_x = body2.position[0] - body1.position[0]
        distance_y = body2.position[1] - body1.position[1]
        distance = math.sqrt(distance_x**2 + distance_y**2 + softening)

        if distance == 0:
            return (0,0)
        force_magnitude = G * body1.mass * body2.mass / distance**2
        force_x = force_magnitude * (distance_x / distance)
        force_y = force_magnitude * (distance_y / distance)
        return (force_x, force_y)

    @staticmethod
    def set_estimated_initial_velocity(planet, central_body, G = 0.1):
        dx = planet.position[0] - central_body.position[0]
        dy = planet.position[1] - central_body.position[1]
        distance = math.sqrt(dx**2 + dy**2)

        if distance == 0:
            return

        orbital_velocity = morbital_velocity = math.sqrt(G * central_body.mass * distance**2 / (distance**2 + SOFTENING)**1.5)
        velocity_x = -orbital_velocity * (dy / distance)
        velocity_y = orbital_velocity * (dx / distance)
        velocity_x += (random.random() - 0.5) * 0.01
        velocity_y += (random.random() - 0.5) * 0.02
        planet.velocity = [velocity_x, velocity_y]

    @staticmethod
    def set_perfect_initial_velocity(planet, central_body, G=0.1):
        dx = planet.position[0] - central_body.position[0]
        dy = planet.position[1] - central_body.position[1]
        distance = math.sqrt(dx**2 + dy**2)

        if distance == 0:
            return

        orbital_velocity = math.sqrt(G * central_body.mass / distance)

        planet.velocity = [
            -orbital_velocity * (dy / distance) + central_body.velocity[0],
             orbital_velocity * (dx / distance) + central_body.velocity[1]
        ]

    @staticmethod
    def check_boundary(body, sun, width, height):
        dx = body.position[0] - sun.position[0]
        dy = body.position[1] - sun.position[1]
        distance = math.sqrt(dx**2 + dy**2)

        MAX_DISTANCE = max(width, height) * 50
        return distance > MAX_DISTANCE

    _glow_cache = {}
    
    @staticmethod
    def create_glow_surface(radius, color, intensity = 100):
        key = (radius, color, intensity)
        if key not in Helper._glow_cache:
            if len(Helper._glow_cache) > 64:
                Helper._glow_cache.clear()
            
            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            for r in range(radius, 0, -2):
                alpha = int(intensity * (r / radius) ** 2)
                pygame.draw.circle(surf, (*color, alpha), (radius, radius), r)
            
            Helper._glow_cache[key] = surf
        return Helper._glow_cache[key]
    
    @staticmethod
    def check_collision(body1, body2):
        dx = body2.position[0] - body1.position[0]
        dy = body2.position[1] - body1.position[1]
        distance = math.sqrt(dx**2 + dy**2)

        return distance < (body1.radius + body2.radius)

    @staticmethod
    def resolve_elastic_collision(body1, body2):
        dx = body2.position[0] - body1.position[0]
        dy = body2.position[1] - body1.position[1]
        distance = math.sqrt(dx**2 + dy**2)

        if distance == 0:
            return
        
        normal_x = dx / distance
        normal_y = dy / distance

        relative_velocity_x = body2.velocity[0] - body1.velocity[0]
        relative_velocity_y = body2.velocity[1] - body1.velocity[1]

        velocity_along_normal = relative_velocity_x * normal_x + relative_velocity_y * normal_y

        if velocity_along_normal > 0:
            return

        restitution = 0.9
        impulse_magnitude = -(1 + restitution) * velocity_along_normal
        impulse_magnitude /= (1 / body1.mass + 1 / body2.mass)
        impulse_x = impulse_magnitude * normal_x
        impulse_y = impulse_magnitude * normal_y    

        body1.velocity[0] -= impulse_x / body1.mass
        body1.velocity[1] -= impulse_y / body1.mass

        body2.velocity[0] += impulse_x / body2.mass
        body2.velocity[1] += impulse_y / body2.mass

    @staticmethod
    def resolve_inelastic_collision(body1, body2, bodies):
        from specialized_bodies import BlackHole, Star, Planet

        total_mass = body1.mass + body2.mass
        if total_mass == 0:
            return bodies

        vx = (body1.velocity[0] * body1.mass + body2.velocity[0] * body2.mass) / total_mass
        vy = (body1.velocity[1] * body1.mass + body2.velocity[1] * body2.mass) / total_mass
        px = (body1.position[0]*body1.mass + body2.position[0]*body2.mass) / total_mass
        py = (body1.position[1]*body1.mass + body2.position[1]*body2.mass) / total_mass

        new_radius = int(math.sqrt(body1.radius**2 + body2.radius**2))
        new_color = tuple(int((c1*body1.mass + c2*body2.mass) / total_mass) for c1, c2 in zip(body1.color, body2.color))

        pos = [px, py]

        if isinstance(body1, BlackHole) or isinstance(body2, BlackHole):
            new_body = BlackHole(f"{body1.name}-{body2.name}", total_mass, new_radius, new_color, pos)
        elif isinstance(body1, Star) or isinstance(body2, Star):
            stars = [b for b in (body1, body2) if isinstance(b, Star)]
            star = max(stars, key=lambda s: s.mass)
            new_body = Star(star.name, total_mass, new_radius, new_color, pos)
            new_body.age = star.age
            new_body.lifetime = star.lifetime 
        else: 
            new_body = Planet(f"{body1.name}-{body2.name}", total_mass, new_radius, new_color, pos)
        
        new_body.velocity = [vx, vy]

        if body1 in bodies: bodies.remove(body1)
        if body2 in bodies: bodies.remove(body2)
        bodies.append(new_body)
        return bodies
    
    @staticmethod
    def rk4_step(bodies, dt):
        masses = [body.mass for body in bodies]
        pos0 = [body.position[:] for body in bodies]
        vel0 = [body.velocity[:] for body in bodies]

        acc1 = Helper.get_accelerations(pos0, masses)

        pos2 = [[p[0] + v[0]*dt/2, p[1] + v[1]*dt/2] for p, v in zip(pos0, vel0)]
        vel2 = [[v[0] + a[0]*dt/2, v[1] + a[1]*dt/2] for v, a in zip(vel0, acc1)]
        acc2 = Helper.get_accelerations(pos2, masses)

        pos3 = [[p[0] + v[0]*dt/2, p[1] + v[1]*dt/2] for p, v in zip(pos0, vel2)]
        vel3 = [[v[0] + a[0]*dt/2, v[1] + a[1]*dt/2] for v, a in zip(vel0, acc2)]
        acc3 = Helper.get_accelerations(pos3, masses)

        pos4 = [[p[0] + v[0]*dt, p[1] + v[1]*dt] for p, v in zip(pos0, vel3)]
        vel4 = [[v[0] + a[0]*dt, v[1] + a[1]*dt] for v, a in zip(vel0, acc3)]
        acc4 = Helper.get_accelerations(pos4, masses)

        for i, b in enumerate(bodies):
            b.position[0] = pos0[i][0] + (dt/6) * (vel0[i][0] + 2*vel2[i][0] + 2*vel3[i][0] + vel4[i][0])
            b.position[1] = pos0[i][1] + (dt/6) * (vel0[i][1] + 2*vel2[i][1] + 2*vel3[i][1] + vel4[i][1])
            b.velocity[0] = vel0[i][0] + (dt/6) * (acc1[i][0] + 2*acc2[i][0] + 2*acc3[i][0] + acc4[i][0])
            b.velocity[1] = vel0[i][1] + (dt/6) * (acc1[i][1] + 2*acc2[i][1] + 2*acc3[i][1] + acc4[i][1])
