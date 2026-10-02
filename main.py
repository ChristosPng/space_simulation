import pygame
import math
import sys
from celestial_body import CelestialBody
from helper import Helper
from cosmic_dust import CosmicDust
from specialized_bodies import *
from particle import Particle
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class _Silent:
    def play(self, *a, **k): pass

impact_sound = pause_sound = dt_change_sound = _Silent()

def handle_audio():
    global impact_sound, pause_sound, dt_change_sound

    def path(name):
        return os.path.join(BASE_DIR, "sounds", name)

    def load_sound(name):
        try:
            return pygame.mixer.Sound(path(name))
        except (pygame.error, FileNotFoundError) as e:
            print(f"Sound '{name}' disabled: {e}")
            return _Silent()

    try:
        pygame.mixer.init()
    except pygame.error as e:
        print(f"Audio disabled: {e}")
        return

    try:
        pygame.mixer.music.load(path("backround.mp3"))
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(-1)
    except (pygame.error, FileNotFoundError) as e:
        print(f"Music disabled: {e}")

    impact_sound = load_sound("impact.mp3")
    pause_sound = load_sound("pause.mp3")
    dt_change_sound = load_sound("dt.mp3")

pygame.init()

info = pygame.display.Info()
WIDTH = info.current_w
HEIGHT = info.current_h

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Orbital System Simulation")

zoom = 1.0

camera_x = WIDTH // 2
camera_y = HEIGHT // 2

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Orbital System Simulation")

num_stars = 400
stars = [CosmicDust(WIDTH, HEIGHT) for _ in range(num_stars)]

planet_list = []

sun = Star("Sun", 100000, 60, (255, 150, 0), [WIDTH//2, HEIGHT//2])
earth = Planet("Earth", 1000, 15, (0, 100, 255), [WIDTH//2 + 900, HEIGHT//2])
moon = Moon("Moon", 5, 5, (200, 200, 200), [WIDTH//2 + 940, HEIGHT//2], earth)
p1 = Planet("Ares", 300, 10, (200, 100, 100), [WIDTH//2 - 1000, HEIGHT//2])
p2 = Planet("Jupiter", 700, 25, (200, 180, 150), [WIDTH//2 + 1200, HEIGHT//2 - 300])
p3 = Planet("Neptune", 600, 18, (100, 100, 255), [WIDTH//2 + 1600, HEIGHT//2])
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
small_font = pygame.font.SysFont(None, 20)
font = pygame.font.SysFont(None, 24)
handle_audio()

clock = pygame.time.Clock()
up_sound_played = False
down_sound_played = False

all_particles = []

dt = 0.1
STEP = 0.5

#code for gui planet arrangement
spawning = False
spawn_start_pos = (0,0)
spawn_types = ["Planet", "Star", "BlackHole"]
spawn_type_idx = 0 #default to planet

type_defaults = {
    "Planet": {"mass": 500, "radius": 12, "color": (0, 255, 150)},
    "Star": {"mass": 80000, "radius": 50, "color": (255, 200, 50)},
    "BlackHole": {"mass": 65000, "radius": 30, "color": (30, 30, 30)}
}

spawn_mass = type_defaults[spawn_types[spawn_type_idx]]["mass"]
spawn_radius = type_defaults[spawn_types[spawn_type_idx]]["radius"]
spawn_color = type_defaults[spawn_types[spawn_type_idx]]["color"]

custom_count = 1

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
                pause_sound.play()

            if event.key in (pygame.K_F11, pygame.K_f): #use "F11" or "f" key to toggle fullscreen
                pygame.display.toggle_fullscreen() 

            if event.key == pygame.K_t:  #use "T" key to toggle spawn type
                spawn_type_idx = (spawn_type_idx + 1) % len(spawn_types)
                spawn_mass = type_defaults[spawn_types[spawn_type_idx]]["mass"]
                spawn_radius = type_defaults[spawn_types[spawn_type_idx]]["radius"]
                spawn_color = type_defaults[spawn_types[spawn_type_idx]]["color"]

            if event.key == pygame.K_LEFTBRACKET:  #use "[" key to decrease spawn mass
                spawn_mass = max(1, spawn_mass - 10)
            if event.key == pygame.K_RIGHTBRACKET: #use "]" key to increase spawn mass
                spawn_mass += 50

            if event.key == pygame.K_MINUS:  #use "-" key to decrease spawn radius
                spawn_radius = max(2, spawn_radius - 2)
            if event.key == pygame.K_EQUALS: #use "=" key to increase spawn radius
                spawn_radius += 2

        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                zoom *= 1.1
            else:
                zoom *= 0.9
            zoom = max(0.05, min(10.0, zoom))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            spawning = True
            spawn_start_pos = pygame.mouse.get_pos()   
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 3 and spawning:
            spawning = False
            end_pos = event.pos
            world_x = (spawn_start_pos[0] - WIDTH // 2) / zoom + camera_x
            world_y = (spawn_start_pos[1] - HEIGHT // 2) / zoom + camera_y

            vx = (spawn_start_pos[0] - end_pos[0]) * 0.02 / zoom
            vy = (spawn_start_pos[1] - end_pos[1]) * 0.02 / zoom

            obj_type = spawn_types[spawn_type_idx]
            name = f"Custom_{obj_type}_{custom_count}"
            custom_count += 1

            if obj_type == "Star":
                new_body = Star(name, spawn_mass, spawn_radius, spawn_color, [world_x, world_y])
            elif obj_type == "BlackHole":
                new_body = BlackHole(name, spawn_mass, spawn_radius, (0, 0, 0), [world_x, world_y])
            else:
                new_body = Planet(name, spawn_mass, spawn_radius, spawn_color, [world_x, world_y])

            new_body.velocity = [vx, vy]
            planet_list.append(new_body)

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

        n = max(1, math.ceil(dt / STEP))
        for _ in range(n):
            Helper.rk4_step(planet_list, dt / n)      

        collision_pairs = []
        for i in range(len(planet_list)):
            for j in range(i + 1, len(planet_list)):
                body1 = planet_list[i]
                body2 = planet_list[j]
                if Helper.check_collision(body1, body2):
                    collision_pairs.append((body1, body2))
                        

        merged = set()
        for body1, body2 in collision_pairs:
            if body1 in merged or body2 in merged:
                continue
            merged.add(body1)
            merged.add(body2)
            impact_sound.play()

            impact_x = (body1.position[0] + body2.position[0]) / 2
            impact_y = (body1.position[1] + body2.position[1]) / 2

            for _ in range(100):
                p_color = [(c1 + c2) // 2 for c1, c2 in zip(body1.color, body2.color)]
                all_particles.append(Particle(impact_x, impact_y, p_color))


            planet_list = Helper.resolve_inelastic_collision(body1, body2, planet_list)

        stars_alive = [b for b in planet_list if isinstance(b, Star)]
        if stars_alive:
            sun = max(stars_alive, key=lambda s: s.mass)
            for body in planet_list[:]:
                if Helper.check_boundary(body, sun, WIDTH, HEIGHT):
                    print(f"{body.name} has left the simulation area.")
                    planet_list.remove(body)

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

        for particle in all_particles[:]:
            particle.update()
            if particle.life <= 0:
                all_particles.remove(particle)

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
        planet.draw(screen, planet_list, zoom, camera_x, camera_y, WIDTH, HEIGHT)

    for particle in all_particles[:]:
        particle.draw(screen, zoom, camera_x, camera_y, WIDTH, HEIGHT) 


    dt_text = font.render(f"Time Step: {dt:.1f}", True, (255, 255, 255))
    screen.blit(dt_text, (10, 10))

    if spawning:
        current_mouse = pygame.mouse.get_pos()
        pygame.draw.line(screen, (255, 255, 255), spawn_start_pos, current_mouse, 2)
        preview_radius = max(2, int(spawn_radius * zoom))
        pygame.draw.circle(screen, spawn_color, spawn_start_pos, preview_radius)

    dt_text = font.render(f"Time Step: {dt:.1f}", True, (255, 255, 255))
    screen.blit(dt_text, (10, 10))

    hud_lines = [
        f"Selected Type [T]: {spawn_types[spawn_type_idx]}",
        f"Spawn Mass [[ / ]]: {spawn_mass}",
        f"Spawn Radius [- / =]: {spawn_radius}",
        "Right-Click + Drag: Launch Body"
    ]

    for idx, line in enumerate(hud_lines):
        txt = small_font.render(line, True, (200, 220, 255))
        screen.blit(txt, (10, 35 + idx * 18))

    if paused:
        pause = font.render("PAUSED - Press SPACE to Resume", True, (255, 100, 0))
        pygame.draw.rect(screen, (255, 255, 255), (WIDTH // 2 - pause.get_width() // 2 - 10, HEIGHT // 8 - 10, pause.get_width() + 20, pause.get_height() + 20))
        screen.blit(pause, (WIDTH // 2 - pause.get_width() // 2, HEIGHT // 8 ))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
