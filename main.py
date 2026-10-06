import pygame
import math
import sys
from celestial_body import CelestialBody
from helper import Helper
from specialized_bodies import *
from particle import Particle
import os
import native_physics
from menu import run_menu
from starfield import ParallaxStars
import terrain

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

starfield = ParallaxStars(WIDTH, HEIGHT)

def orbit_pos(distance, angle_deg):
    a = math.radians(angle_deg)
    return [WIDTH//2 + distance * math.cos(a), HEIGHT//2 + distance * math.sin(a)]

def build_solar_system():
    sun = Star("Sun", 100000, 60, (255, 150, 0), [WIDTH//2, HEIGHT//2])
    earth = Planet("Earth", 1000, 15, (0, 100, 255), orbit_pos(900, 0))
    moon = Moon("Moon", 5, 5, (200, 200, 200), [earth.position[0] + 40, earth.position[1]], earth)
    p1 = Planet("Ares", 100, 10, (200, 100, 100), orbit_pos(400, 180))
    p2 = Planet("Jupiter", 700, 25, (200, 180, 150), orbit_pos(1800, 100))
    p3 = Planet("Neptune", 300, 18, (100, 100, 255), orbit_pos(3000, 250))
    bodies = [sun, earth, moon, p1, p2, p3]

    for body in bodies:
        if not isinstance(body, Star) and not isinstance(body, Moon):
            Helper.set_perfect_initial_velocity(body, sun)
    for body in bodies:
        if isinstance(body, Moon):
            Helper.set_perfect_initial_velocity(body, body.orb_planet)

    px = sum(b.mass * b.velocity[0] for b in bodies if b is not sun)
    py = sum(b.mass * b.velocity[1] for b in bodies if b is not sun)
    sun.velocity = [-px / sun.mass, -py / sun.mass]

    for body in bodies:
        body.velocity[0] += 1
        body.velocity[1] += 1
    return bodies

handle_audio()

choice = run_menu(screen, WIDTH, HEIGHT,
                  footer=f"Physics engine: {'C++' if native_physics.available else 'Python'}")

if choice == "quit":
    pygame.quit()
    sys.exit()

planet_list = build_solar_system() if choice == "start" else []
zoom = 0.25 if choice == "start" else 1.0

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
    "Planet": {"mass": 500, "radius": 12, "color": (0, 255, 150), "max_mass": 10000, "max_radius": 40},
    "Star": {"mass": 80000, "radius": 50, "color": (255, 200, 50), "max_mass": 5000000, "max_radius": 250},
    "BlackHole": {"mass": 300000, "radius": 30, "color": (30, 30, 30), "max_mass": 20000000, "max_radius": 100}
}

spawn_mass = type_defaults[spawn_types[spawn_type_idx]]["mass"]
spawn_radius = type_defaults[spawn_types[spawn_type_idx]]["radius"]
spawn_color = type_defaults[spawn_types[spawn_type_idx]]["color"]

custom_count = 1
menu_btn = pygame.Rect(WIDTH - 160, 10, 150, 38)

dragging = False
follow_cam = True

while running:
    back_to_menu = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
                pause_sound.play()

            if event.key in (pygame.K_F11, pygame.K_f): #use "F11" or "f" key to toggle fullscreen
                pygame.display.toggle_fullscreen() 

            if event.key == pygame.K_c:  #use "C" for camera to follow the system
                follow_cam = True

            if event.key == pygame.K_t:  #use "T" key to toggle spawn type
                spawn_type_idx = (spawn_type_idx + 1) % len(spawn_types)
                spawn_mass = type_defaults[spawn_types[spawn_type_idx]]["mass"]
                spawn_radius = type_defaults[spawn_types[spawn_type_idx]]["radius"]
                spawn_color = type_defaults[spawn_types[spawn_type_idx]]["color"]

            if event.key == pygame.K_LEFTBRACKET: #use "[" to decrease mass
                mag = 10 ** (len(str(int(spawn_mass))) - 1)
                if spawn_mass == mag:
                    mag = max(1, mag // 10)
                spawn_mass = max(1, spawn_mass - mag)

            if event.key == pygame.K_RIGHTBRACKET: #use "[" to increase mass
                max_m = type_defaults[spawn_types[spawn_type_idx]]["max_mass"]
                mag = 10 ** (len(str(int(spawn_mass))) - 1)
                spawn_mass = min(max_m, spawn_mass + mag)

            if event.key == pygame.K_MINUS: #use "-" to decrease radius
                spawn_radius = max(2, spawn_radius - 2)

            if event.key == pygame.K_EQUALS: ##use "+" to increase radius
                max_r = type_defaults[spawn_types[spawn_type_idx]]["max_radius"]
                spawn_radius = min(max_r, spawn_radius + 2)

        if event.type == pygame.MOUSEWHEEL:
            old_zoom = zoom
            if event.y > 0:
                zoom *= 1.1
            else:
                zoom *= 0.9
            zoom = max(0.05, min(10.0, zoom))

            if not follow_cam:
                mx, my = pygame.mouse.get_pos()
                camera_x += (mx - WIDTH // 2) * (1 / old_zoom - 1 / zoom)
                camera_y += (my - HEIGHT // 2) * (1 / old_zoom - 1 / zoom)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if menu_btn.collidepoint(event.pos):
                back_to_menu = True
            else:
                dragging = True
        
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            dragging = False

        if event.type == pygame.MOUSEMOTION and dragging:
            if event.buttons[0]:
                follow_cam = False                 
                camera_x -= event.rel[0] / zoom
                camera_y -= event.rel[1] / zoom
            else:
                dragging = False

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
    
    if back_to_menu:
        camera_x, camera_y = WIDTH // 2, HEIGHT // 2
        follow_cam = True
        dragging = False
        all_particles = []
        choice = run_menu(screen, WIDTH, HEIGHT,
                          footer=f"Physics engine: {'C++' if native_physics.available else 'Python'}")
        if choice == "quit":
            running = False
            continue
        planet_list = build_solar_system() if choice == "start" else []
        zoom = 0.25 if choice == "start" else 1.0
        camera_x, camera_y = WIDTH // 2, HEIGHT // 2
        all_particles = []
        paused = False
        spawning = False
        dt = 0.1
        custom_count = 1

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
        if not native_physics.step(planet_list, dt, n):
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

        total_m = sum(b.mass for b in planet_list)
        if total_m > 0:
            com_x = sum(b.position[0] * b.mass for b in planet_list) / total_m
            com_y = sum(b.position[1] * b.mass for b in planet_list) / total_m
            limit = max(WIDTH, HEIGHT) * 150          # was 50 (measured from the sun)
            for body in planet_list[:]:
                dist = math.hypot(body.position[0] - com_x, body.position[1] - com_y)
                if dist > limit:
                    print(f"{body.name[:30]} left the simulation area ({dist:.0f} from system center)")
                    planet_list.remove(body)

        for planet in planet_list:
            planet.update(dt)

        for body in planet_list:
            if isinstance(body, BlackHole):
                removed = body.attract(planet_list)
                for r in removed:
                    if r in planet_list:
                        planet_list.remove(r)


        for particle in all_particles[:]:
            particle.update()
            if particle.life <= 0:
                all_particles.remove(particle)

    screen.fill((0, 0, 0))

    if follow_cam:
        total_mass = sum(body.mass for body in planet_list)
        if total_mass > 0:
            target_x = sum(body.position[0] * body.mass for body in planet_list) / total_mass
            target_y = sum(body.position[1] * body.mass for body in planet_list) / total_mass

            camera_x += (target_x - camera_x) * 0.01
            camera_y += (target_y - camera_y) * 0.01
        else:
            camera_x += (WIDTH//2 - camera_x)
            camera_y += (HEIGHT//2 - camera_y) 

    starfield.draw(screen, camera_x, camera_y, zoom)
    
    terrain.begin_frame()
    for planet in planet_list[:]:
        planet.draw(screen, planet_list, zoom, camera_x, camera_y, WIDTH, HEIGHT)

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


    hud_lines = [
        f"Selected Type [T]: {spawn_types[spawn_type_idx]}",
        f"Spawn Mass [[ / ]]: {spawn_mass}",
        f"Spawn Radius [- / =]: {spawn_radius}",
        "Right-Click + Drag: Launch Body",
        f"Physics Engine: {'C++' if native_physics.available else 'Python'}",
        f"Camera [C]: {'Following' if follow_cam else 'Free (left-drag to pan)'}",
        f"Terrain: {'C++' if terrain.available else 'off (flat planets)'}",
    ]

    for idx, line in enumerate(hud_lines):
        txt = font.render(line, True, (200, 220, 255))
        screen.blit(txt, (10, 35 + idx * 24))

    hovered = menu_btn.collidepoint(pygame.mouse.get_pos())
    pygame.draw.rect(screen, (45, 60, 105) if hovered else (22, 28, 48), menu_btn, border_radius=10)
    pygame.draw.rect(screen, (255, 170, 60) if hovered else (60, 70, 100), menu_btn, width=2, border_radius=10)
    label = font.render("Main Menu", True, (255, 255, 255) if hovered else (210, 225, 255))
    screen.blit(label, label.get_rect(center=menu_btn.center))

    if paused:
        pause = font.render("PAUSED - Press SPACE to Resume", True, (255, 100, 0))
        pygame.draw.rect(screen, (255, 255, 255), (WIDTH // 2 - pause.get_width() // 2 - 10, HEIGHT // 8 - 10, pause.get_width() + 20, pause.get_height() + 20))
        screen.blit(pause, (WIDTH // 2 - pause.get_width() // 2, HEIGHT // 8 ))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
