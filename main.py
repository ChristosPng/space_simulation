import pygame
import math
import sys
from celestial_body import CelestialBody
from helper import Helper
from cosmic_dust import CosmicDust
from specialized_bodies import *
from particle import Particle

def handle_audio():
    pygame.mixer.init()

    pygame.mixer.music.load('sounds/backround.mp3')
    pygame.mixer.music.set_volume(0.4)
    pygame.mixer.music.play(-1)

    global impact_sound, pause_sound, dt_change_sound

    impact_sound = pygame.mixer.Sound('sounds/impact.mp3')

    pause_sound = pygame.mixer.Sound('sounds/pause.mp3')

    dt_change_sound = pygame.mixer.Sound('sounds/dt.mp3')

pygame.init()

zoom = 1.0

WIDTH = 1500
HEIGHT = 800

camera_x = WIDTH // 2
camera_y = HEIGHT // 2

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Orbital System Simulation")

num_stars = 400
stars = [CosmicDust(WIDTH, HEIGHT) for _ in range(num_stars)]

planet_list = []

sun = Star("Sun", 100000, 60, (255, 150, 0), [WIDTH//2, HEIGHT//2])
earth = Planet("Earth", 1000, 15, (0, 100, 255), [WIDTH//2 + 800, HEIGHT//2])
moon = Moon("Moon", 5, 5, (200, 200, 200), [WIDTH//2 + 840, HEIGHT//2], earth)
p1 = Planet("Ares", 300, 10, (200, 100, 100), [WIDTH//2 - 1000, HEIGHT//2])
p2 = Planet("Jupiter", 3000, 25, (200, 180, 150), [WIDTH//2 + 900, HEIGHT//2])
p3 = Planet("Neptune", 600, 18, (100, 100, 255), [WIDTH//2 + 1200, HEIGHT//2])
bh = BlackHole("Black Hole", 65000, 30, (0, 0, 0), [WIDTH//2 + 6000, HEIGHT//2 - 400])
bh2 = BlackHole("Black Hole", 65000, 30, (0, 0, 0), [WIDTH//2 - 7000, HEIGHT//2 - 400])

planet_list.append(sun)
planet_list.append(earth)
planet_list.append(moon)
planet_list.append(p1)
planet_list.append(p2)
planet_list.append(p3)

sun.velocity = [2, 0]



for body in planet_list:
   if not isinstance(body, Star) and not isinstance(body, Moon):
        Helper.set_perfect_initial_velocity(body, sun)

for body in planet_list:
    if isinstance(body, Moon):
        Helper.set_perfect_initial_velocity(body, body.orb_planet)


running = True
paused = False
font = pygame.font.SysFont(None, 24)
handle_audio()

clock = pygame.time.Clock()
up_sound_played = False
down_sound_played = False

all_particles = []

dt = 0.1
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
                pause_sound.play()

        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                zoom *= 1.1
            else:
                zoom *= 0.9
            zoom = max(0.05, min(10.0, zoom))

    keys = pygame.key.get_pressed()

    if keys[pygame.K_UP]:
        dt = min(8.0, dt + 0.1)
        if not up_sound_played:
            dt_change_sound.play()
            up_sound_played = True
    else:
        up_sound_played = False

    if keys[pygame.K_DOWN]:
        dt = max(0.1, dt - 0.1)
        if not down_sound_played:
            dt_change_sound.play()
            down_sound_played = True
    else:
        down_sound_played = False

        
    if not paused:

        masses = [body.mass for body in planet_list]
        pos0 = [body.position for body in planet_list]
        vel0 = [body.velocity for body in planet_list]

        acc1 = Helper.get_accelerations(pos0, masses)

        pos2 = [[p[0] + v[0] * dt/2, p[1] + v[1] * dt/2] for p, v in zip(pos0, vel0)]
        vel2 = [[v[0] + a[0] * dt/2, v[1] + a[1] * dt/2] for v, a in zip(vel0, acc1)]
        acc2 = Helper.get_accelerations(pos2, masses)

        pos3 = [[p[0] + v[0] * dt/2, p[1] + v[1] * dt/2] for p, v in zip(pos0, vel2)]
        vel3 = [[v[0] + a[0] * dt/2, v[1] + a[1] * dt/2] for v, a in zip(vel0, acc2)]
        acc3 = Helper.get_accelerations(pos3, masses)

        pos4 = [[p[0] + v[0] * dt, p[1] + v[1] * dt] for p, v in zip(pos0, vel3)]
        vel4 = [[v[0] + a[0] * dt, v[1] + a[1] * dt] for v, a in zip(vel0, acc3)]
        acc4 = Helper.get_accelerations(pos4, masses)

        for i, body in enumerate(planet_list):
            body.position[0] += (dt/6) * (vel0[i][0] + 2*vel2[i][0] + 2*vel3[i][0] + vel4[i][0])
            body.position[1] += (dt/6) * (vel0[i][1] + 2*vel2[i][1] + 2*vel3[i][1] + vel4[i][1])
            
            body.velocity[0] += (dt/6) * (acc1[i][0] + 2*acc2[i][0] + 2*acc3[i][0] + acc4[i][0])
            body.velocity[1] += (dt/6) * (acc1[i][1] + 2*acc2[i][1] + 2*acc3[i][1] + acc4[i][1])


        collision_pairs = []

        for i in range(len(planet_list)):
            for j in range(i + 1, len(planet_list)):
                body1 = planet_list[i]
                body2 = planet_list[j]

                if Helper.check_collision(body1, body2):
                    if not (isinstance(body1, BlackHole) and isinstance(body2, BlackHole)):
                        collision_pairs.append((body1, body2))
                        impact_sound.play()

        for body1, body2 in collision_pairs:
            impact_x = (body1.position[0] + body2.position[0]) / 2
            impact_y = (body1.position[1] + body2.position[1]) / 2

            for _ in range(100):
                p_color = [(c1 + c2) // 2 for c1, c2 in zip(body1.color, body2.color)]
                all_particles.append(Particle(impact_x, impact_y, p_color))


            planet_list = Helper.resolve_inelastic_collision(body1, body2, planet_list)

        for body in planet_list:
            if isinstance(body, Star):
                sun = body
        
        for planet in planet_list:
            planet.update(dt)

        for body in planet_list:
            if isinstance(body, BlackHole):
                removed = body.attract(planet_list)
                for r in removed:
                    if r in planet_list:
                        planet_list.remove(r)

        for star in stars:
            star.update()   

    screen.fill((0, 0, 0))

    total_mass = sum(body.mass for body in planet_list)
    if total_mass > 0:
        target_x = sum(body.position[0] * body.mass for body in planet_list) / total_mass
        target_y = sum(body.position[1] * body.mass for body in planet_list) / total_mass

        camera_x += (target_x - camera_x) * 0.01
        camera_y += (target_y - camera_y) * 0.01
    else:
        camera_x += (WIDTH//2 - camera_x) 
        camera_y += (HEIGHT//2 - camera_y) 

    for star in stars:
        star.draw(screen)

    for planet in planet_list[:]:
        if Helper.check_boundary(planet, sun, WIDTH, HEIGHT):
            print(f"{planet.name} has left the simulation area.")
            planet_list.remove(planet)
        planet.draw(screen, planet_list, zoom, camera_x, camera_y, WIDTH, HEIGHT)

    for particle in all_particles[:]:
        particle.update()

        if particle.life <= 0:
            all_particles.remove(particle)
        else:
            particle.draw(screen, zoom, camera_x, camera_y, WIDTH, HEIGHT)

    dt_text = font.render(f"Time Step: {dt:.1f}", True, (255, 255, 255))
    screen.blit(dt_text, (10, 10))

    if paused:
        pause = font.render("PAUSED - Press SPACE to Resume", True, (255, 100, 0))
        pygame.draw.rect(screen, (255, 255, 255), (WIDTH // 2 - pause.get_width() // 2 - 10, HEIGHT // 8 - 10, pause.get_width() + 20, pause.get_height() + 20))
        screen.blit(pause, (WIDTH // 2 - pause.get_width() // 2, HEIGHT // 8 ))
        pygame.display.flip()
        clock.tick(60)
        continue

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
