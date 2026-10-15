import pygame
from specialized_bodies import Star, Planet, BlackHole, Moon
from particle import Particle

class TimelineManager:
    def __init__(self, max_history=600):
        self.history = []
        self.history_index = 0
        self.max_history = max_history

    def _copy_state(self, p_list, p_particles):
        new_planets = []
        old_to_new = {}
        for b in p_list:
            if isinstance(b, Star):
                new_b = Star(b.name, b.mass, b.radius, b.color, list(b.position))
            elif isinstance(b, BlackHole):
                new_b = BlackHole(b.name, b.mass, b.radius, b.color, list(b.position))
                new_b.base_mass = getattr(b, 'base_mass', b.mass)
                new_b.base_radius = getattr(b, 'base_radius', b.radius)
                new_b.event_horizon = getattr(b, 'event_horizon', b.radius * 1.1)
            elif isinstance(b, Moon):
                new_b = Moon(b.name, b.mass, b.radius, b.color, list(b.position), orb_planet=None)
            else:
                new_b = Planet(b.name, b.mass, b.radius, b.color, list(b.position))
            
            new_b.velocity = list(b.velocity)
            if hasattr(b, 'trail'):
                new_b.trail = list(b.trail)
            new_b.surface = None
            new_planets.append(new_b)
            old_to_new[b] = new_b
            
        for old_b, new_b in old_to_new.items():
            if isinstance(old_b, Moon) and old_b.orb_planet in old_to_new:
                new_b.orb_planet = old_to_new[old_b.orb_planet]

        new_particles = []
        for p in p_particles:
            new_p = Particle(p.x, p.y, p.color)
            new_p.vx = p.vx
            new_p.vy = p.vy
            new_p.life = p.life
            new_particles.append(new_p)

        return new_planets, new_particles

    def reset(self, p_list, p_particles):
        self.history = [self._copy_state(p_list, p_particles)]
        self.history_index = 0

    def record(self, p_list, p_particles):
        self.history.append(self._copy_state(p_list, p_particles))
        if len(self.history) > self.max_history:
            self.history.pop(0)
        self.history_index = len(self.history) - 1

    def commit_overwrite(self):
        if self.history:
            self.history = self.history[:self.history_index + 1]

    def step_backward(self, steps=4):
        if self.history:
            self.history_index = max(0, self.history_index - steps)
            return self._copy_state(*self.history[self.history_index])
        return None, None

    def step_forward(self, steps=4):
        if self.history:
            self.history_index = min(len(self.history) - 1, self.history_index + steps)
            return self._copy_state(*self.history[self.history_index])
        return None, None

    def draw_ui(self, screen, font, width):
        bar_w = 600
        bar_h = 8
        bar_x = width // 2 - bar_w // 2
        bar_y = 25
        
        pygame.draw.rect(screen, (40, 45, 60), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        
        if self.history:
            fill_pct = self.history_index / max(1, len(self.history) - 1)
            pygame.draw.rect(screen, (100, 180, 255), (bar_x, bar_y, int(bar_w * fill_pct), bar_h), border_radius=4)
            head_x = bar_x + int(bar_w * fill_pct)
            pygame.draw.circle(screen, (255, 255, 255), (head_x, bar_y + bar_h // 2), 6)
            
        sec_rewound = (max(0, len(self.history) - 1) - self.history_index) / 60.0
        msg = f"PAUSED - Rewound -{sec_rewound:.1f}s (Hold Left/Right to Scrub, SPACE to Resume)"
        txt = font.render(msg, True, (200, 220, 255))
        screen.blit(txt, (width // 2 - txt.get_width() // 2, bar_y + 15))