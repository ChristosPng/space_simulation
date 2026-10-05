import pygame

PANEL = (15, 20, 40, 215)
BTN = (22, 28, 48)
BTN_HOVER = (45, 60, 105)
BTN_BORDER = (60, 70, 100)
ACCENT = (255, 170, 60)
TEXT = (210, 225, 255)
MUTED = (120, 135, 165)

MENU_ITEMS = [
    ("Start Simulation", "start"),
    ("Sandbox (empty space)", "sandbox"),
    ("Controls", "controls"),
    ("Quit", "quit")
]

CONTROLS = [
    ("Space", "Pause / resume"),
    ("Up / Down", "Speed up / slow down time"),
    ("Mouse wheel", "Zoom in / out"),
    ("Right-click + drag", "Launch a new body"),
    ("T", "Cycle body type (planet / star / black hole)"),
    ("[  and  ]", "Decrease / increase spawn mass"),
    ("-  and  =", "Decrease / increase spawn radius"),
    ("F or F11", "Toggle fullscreen"),
    ("Left-click + drag", "Pan the camera"),
    ("C", "Camera follows the system again"),
]

def _draw_background(screen):
    screen.fill((0,0,0))

def _controls_screen(screen, clock, width, height):
    title_font = pygame.font.SysFont(None, int(height * 0.07))
    row_font = pygame.font.SysFont(None, int(height * 0.035))
    hint_font = pygame.font.SysFont(None, int(height * 0.028))

    row_h = int(height * 0.055)
    pw = int(width * 0.5)
    ph = int(height * 0.2) + row_h * len(CONTROLS)
    panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
    pygame.draw.rect(panel, PANEL, panel.get_rect(), border_radius=18)
    px, py = (width - pw) // 2, (height - ph) // 2

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return None

        _draw_background(screen, stars)
        screen.blit(panel, (px, py))

        title = title_font.render("Controls", True, ACCENT)
        screen.blit(title, title.get_rect(centerx=width // 2, y=py + int(height * 0.04)))

        y = py + int(height * 0.04) + title.get_height() + int(height * 0.02)
        for key, desc in CONTROLS:
            screen.blit(row_font.render(key, True, ACCENT), (px + int(pw * 0.08), y))
            screen.blit(row_font.render(desc, True, TEXT), (px + int(pw * 0.40), y))
            y += row_h

        hint = hint_font.render("Press any key or click to go back", True, MUTED)
        screen.blit(hint, hint.get_rect(centerx=width // 2, y=py + ph - int(height * 0.05)))

        pygame.display.flip()
        clock.tick(60)

def run_menu(screen, width, height, footer=""):
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont(None, int(height * 0.11))
    sub_font = pygame.font.SysFont(None, int(height * 0.035))
    btn_font = pygame.font.SysFont(None, int(height * 0.05))
    foot_font = pygame.font.SysFont(None, int(height * 0.026))

    bw, bh, gap = int(width * 0.24), int(height * 0.075), int(height * 0.02)
    top = int(height * 0.45)
    rects = []
    for i in range(len(MENU_ITEMS)):
        r = pygame.Rect(0, 0, bw, bh)
        r.centerx = width // 2
        r.y = top + i * (bh + gap)
        rects.append(r)

    selected = 0
    while True:
        chosen = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.MOUSEMOTION:
                for i, r in enumerate(rects):
                    if r.collidepoint(event.pos):
                        selected = i
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, r in enumerate(rects):
                    if r.collidepoint(event.pos):
                        chosen = MENU_ITEMS[i][1]
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "quit"
                elif event.key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % len(MENU_ITEMS)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % len(MENU_ITEMS)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    chosen = MENU_ITEMS[selected][1]
                elif event.key in (pygame.K_F11, pygame.K_f):
                    pygame.display.toggle_fullscreen()

        if chosen == "controls":
            if _controls_screen(screen, clock, stars, width, height) == "quit":
                return "quit"
        elif chosen:
            return chosen

        _draw_background(screen)

        title = title_font.render("ORBITAL SYSTEM", True, ACCENT)
        title_y = int(height * 0.15)
        screen.blit(title, title.get_rect(centerx=width // 2, y=title_y))
        sub = sub_font.render("N-body gravity sandbox", True, MUTED)
        screen.blit(sub, sub.get_rect(centerx=width // 2, y=title_y + title.get_height() + int(height * 0.01)))

        for i, (label, _) in enumerate(MENU_ITEMS):
            r = rects[i]
            hot = (i == selected)
            pygame.draw.rect(screen, BTN_HOVER if hot else BTN, r, border_radius=12)
            pygame.draw.rect(screen, ACCENT if hot else BTN_BORDER, r, width=2, border_radius=12)
            txt = btn_font.render(label, True, (255, 255, 255) if hot else TEXT)
            screen.blit(txt, txt.get_rect(center=r.center))

        hint = foot_font.render("Up/Down or mouse to select  -  Enter or click to confirm", True, MUTED)
        screen.blit(hint, hint.get_rect(centerx=width // 2, y=height - int(height * 0.08)))
        if footer:
            f = foot_font.render(footer, True, MUTED)
            screen.blit(f, f.get_rect(centerx=width // 2, y=height - int(height * 0.045)))

        pygame.display.flip()
        clock.tick(60)