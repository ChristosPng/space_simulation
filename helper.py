import math
import random
import pygame

BOUNDARY_MARGIN = 200

class Helper:

    @staticmethod
    def get_accelerations(positions, masses):
        accels = [[0,0] for _ in range(len(positions))]
        G = 0.1
        softening = 200

        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                dx = positions[j][0] - positions[i][0]
                dy = positions[j][1] - positions[i][1]
                dist_sq = dx**2 + dy**2 + softening
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

    def set_estimated_initial_velocity(planet, central_body, G = 0.1):
        dx = planet.position[0] - central_body.position[0]
        dy = planet.position[1] - central_body.position[1]
        distance = math.sqrt(dx**2 + dy**2)

        if distance == 0:
            return

        orbital_velocity = math.sqrt(G * central_body.mass / distance) * 0.95
        velocity_x = -orbital_velocity * (dy / distance)
        velocity_y = orbital_velocity * (dx / distance)
        velocity_x += (random.random() - 0.5) * 0.01
        velocity_y += (random.random() - 0.5) * 0.02
        planet.velocity = [velocity_x, velocity_y]

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

    def check_boundary(body, sun, width, height):
        dx = body.position[0] - sun.position[0]
        dy = body.position[1] - sun.position[1]
        distance = math.sqrt(dx**2 + dy**2)

        MAX_DISTANCE = max(width, height) * 50
        return distance > MAX_DISTANCE
    
    def create_glow_surface(radius, color, intensity = 100):
        glow_surface = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
        glow_center = radius * 2
        for i in range(int(radius * 1.5), 0, -1):
            alpha = max(0, min(255, int(intensity * ((1 - (i - radius) / (radius * 1.5)) ** 4))))
            r = max(0, min(255, int(color[0])))
            g = max(0, min(255, int(color[1])))
            b = max(0, min(255, int(color[2])))
            pygame.draw.circle(glow_surface, (r, g, b, alpha), (glow_center, glow_center), i)
        return glow_surface
    
    def check_collision(body1, body2):
        dx = body2.position[0] - body1.position[0]
        dy = body2.position[1] - body1.position[1]
        distance = math.sqrt(dx**2 + dy**2)

        return distance < (body1.radius + body2.radius)

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

    def resolve_inelastic_collision(body1, body2, bodies):
        total_mass = (body1.mass + body2.mass) 
        if total_mass == 0:
            return bodies

        new_velocity_x = (body1.velocity[0] * body1.mass + body2.velocity[0] * body2.mass) / total_mass
        new_velocity_y = (body1.velocity[1] * body1.mass + body2.velocity[1] * body2.mass) / total_mass

        dx = body2.position[0] - body1.position[0]
        dy = body2.position[1] - body1.position[1]
        new_position_x = body1.position[0] + dx/2
        new_position_y = body1.position[1] + dy/2

        new_radius = int(math.sqrt(body1.radius**2 + body2.radius**2))
        
        new_color = (
            (body1.color[0] * body1.mass + body2.color[0] * body2.mass) // total_mass,
            (body1.color[1] * body1.mass + body2.color[1] * body2.mass) // total_mass,
            (body1.color[2] * body1.mass + body2.color[2] * body2.mass) // total_mass
        )

        from specialized_bodies import Star, Planet, BlackHole

        if (isinstance(body1, Star) and isinstance(body2, Star)) or (isinstance(body1, Star) and not isinstance(body2, Star)) or (not isinstance(body1, Star) and isinstance(body2, Star)):
            star = body1 if isinstance(body1, Star) else body2
            other = body2 if isinstance(body1, Star) else body1

            new_body = Star(star.name, total_mass, new_radius, star.color, star.position[:])
            new_body.age = star.age
            new_body.lifetime = star.lifetime 
            new_body.velocity = [new_velocity_x, new_velocity_y]

        if (isinstance(body1, BlackHole) or isinstance(body2, BlackHole)):
            new_body = BlackHole(f"{body1.name}-{body2.name}", total_mass, new_radius, new_color, [new_position_x, new_position_y])
            new_body.velocity = [new_velocity_x, new_velocity_y]


        if isinstance(body1, Planet) and isinstance(body2, Planet):
            new_body = Planet(f"{body1.name}-{body2.name}", total_mass, new_radius, new_color, [new_position_x, new_position_y])
            new_body.velocity = [new_velocity_x, new_velocity_y]

        if body1 in bodies: bodies.remove(body1)
        if body2 in bodies: bodies.remove(body2)
        bodies.append(new_body)
        
        return bodies

