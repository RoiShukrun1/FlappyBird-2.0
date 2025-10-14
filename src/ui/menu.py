import pygame
import sys
import os
import math
import random
from ..core.assets import BG_IMG, SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL, PIPE_IMG, BIRD_IMGS
from .button import Button, render_outlined_text
from .registration import run_registration, register_user_to_mongo
from .login import run_login
from ..multiplayer.leaderboard_client import fetch_top10, submit_score, fetch_user_best, run_leaderboard_screen  # <-- added screen

# Initialize pygame
pygame.init()

WIN_WIDTH = 800
WIN_HEIGHT = 900
WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Flappy Bird Menu")

BUTTON_WIDTH = 320
BUTTON_HEIGHT = 60
BUTTON_MARGIN = 20

class AnimatedElement:
    def __init__(self, x, y, speed, image=None, color=None, size=None):
        self.x = x
        self.y = y
        self.speed = speed
        self.image = image
        self.color = color
        self.size = size
        self.angle = 0
        self.original_y = y
        
    def update(self, dt):
        self.x += self.speed * dt
        self.angle += 0.5 * dt
        if self.x > WIN_WIDTH + 50:
            self.x = -50
        if self.image is None:
            self.y = self.original_y + math.sin(self.angle * 0.5) * 10

# ---------- Tiny UI helpers for left-side chips ----------
def _draw_left_chip(surface, label, y, dot_color=None):
    """Generic left-side chip; returns its rect."""
    pad_x = 12
    chip_h = 36
    font = pygame.font.Font(None, 24)
    txt = font.render(label, True, (255, 255, 255))
    left_pad = 28 if dot_color else 12
    chip_w = left_pad + txt.get_width() + 12
    chip_rect = pygame.Rect(pad_x, y, chip_w, chip_h)

    s = pygame.Surface((chip_rect.w, chip_rect.h), pygame.SRCALPHA)
    pygame.draw.rect(s, (0, 0, 0, 140), s.get_rect(), border_radius=18)
    pygame.draw.rect(s, (255, 255, 255, 180), s.get_rect(), width=1, border_radius=18)
    if dot_color:
        pygame.draw.circle(s, dot_color, (16, chip_h // 2), 6)
        s.blit(txt, (28, (chip_h - txt.get_height()) // 2))
    else:
        s.blit(txt, (12, (chip_h - txt.get_height()) // 2))
    surface.blit(s, chip_rect.topleft)
    return chip_rect

def draw_leaderboard_chip(surface) -> pygame.Rect:
    return _draw_left_chip(surface, "Leaderboard", 12, (255, 200, 0))

def draw_host_chip(surface, y_start) -> pygame.Rect:
    return _draw_left_chip(surface, "Host Game", y_start, (80, 220, 120))

def draw_join_chip(surface, y_start) -> pygame.Rect:
    return _draw_left_chip(surface, "Join Game", y_start, (80, 160, 255))

def draw_user_chip(surface, label: str | None) -> pygame.Rect:
    win_w, _ = surface.get_size()
    pad = 12
    chip_h = 36
    font = pygame.font.Font(None, 24)
    text = "Sign in" if not label else label
    txt = font.render(text, True, (255, 255, 255))
    left_pad = 12 if not label else 28
    chip_w = left_pad + txt.get_width() + 12
    chip_rect = pygame.Rect(win_w - chip_w - pad, pad, chip_w, chip_h)
    s = pygame.Surface((chip_rect.w, chip_rect.h), pygame.SRCALPHA)
    pygame.draw.rect(s, (0, 0, 0, 140), s.get_rect(), border_radius=18)
    pygame.draw.rect(s, (255, 255, 255, 180), s.get_rect(), width=1, border_radius=18)
    if label:
        pygame.draw.circle(s, (40, 200, 90), (16, chip_h // 2), 6)
        s.blit(txt, (28, (chip_h - txt.get_height()) // 2))
    else:
        s.blit(txt, (12, (chip_h - txt.get_height()) // 2))
    surface.blit(s, chip_rect.topleft)
    return chip_rect

# ---------- Minimal text input overlay (kept here if you need later) ----------
def prompt_text(surface, title, initial_text="", placeholder="", max_len=64):
    """Very small modal text prompt. Returns text or None if canceled."""
    clock = pygame.time.Clock()
    font_title = pygame.font.Font(None, 36)
    font = pygame.font.Font(None, 28)
    text = list(initial_text)
    cursor_visible = True
    blink = 0

    overlay = pygame.Surface((WIN_WIDTH, WIN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))

    box_w, box_h = 500, 150
    box = pygame.Rect((WIN_WIDTH - box_w)//2, (WIN_HEIGHT - box_h)//2, box_w, box_h)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    entered = "".join(text).strip()
                    return entered if entered else None
                elif event.key == pygame.K_BACKSPACE:
                    if text:
                        text.pop()
                else:
                    if event.unicode and len(text) < max_len and (32 <= ord(event.unicode) < 127):
                        text.append(event.unicode)

        blink = (blink + 1) % 60
        cursor_visible = blink < 30

        # Draw modal
        surface.blit(overlay, (0, 0))
        pygame.draw.rect(surface, (240, 240, 240), box, border_radius=10)
        pygame.draw.rect(surface, (50, 50, 50), box, 2, border_radius=10)

        # Title
        title_surf = pygame.font.Font(None, 36).render(title, True, (20, 20, 20))
        surface.blit(title_surf, (box.centerx - title_surf.get_width()//2, box.y + 16))

        # Input line
        typed = "".join(text)
        display = typed if typed else ""
        color = (20, 20, 20)
        line = font.render(display, True, color)
        line_x = box.x + 24
        line_y = box.y + 72
        surface.blit(line, (line_x, line_y))

        # Cursor
        if cursor_visible and len(typed) < max_len:
            cx = line_x + line.get_width() + 2
            cy = line_y + 3
            pygame.draw.line(surface, (20, 20, 20), (cx, cy), (cx, cy + 20), 2)

        pygame.display.update()
        clock.tick(60)

# ---------- Menu drawing / logic ----------
def create_background_elements():
    elements = []
    for i in range(5):
        x = random.randint(-100, WIN_WIDTH + 100)
        y = random.randint(50, 200)
        speed = random.uniform(10, 30)
        elements.append(AnimatedElement(x, y, speed))
    for i in range(3):
        x = random.randint(-100, WIN_WIDTH + 100)
        y = random.randint(300, 600)
        speed = random.uniform(20, 40)
        elements.append(AnimatedElement(x, y, speed, PIPE_IMG))
    return elements

def draw_cloud(surface, x, y, size=30):
    cloud_color = (255, 255, 255, 180)
    pygame.draw.circle(surface, cloud_color, (int(x), int(y)), size)
    pygame.draw.circle(surface, cloud_color, (int(x + size*0.7), int(y)), int(size*0.8))
    pygame.draw.circle(surface, cloud_color, (int(x - size*0.7), int(y)), int(size*0.8))
    pygame.draw.circle(surface, cloud_color, (int(x + size*0.3), int(y - size*0.5)), int(size*0.6))
    pygame.draw.circle(surface, cloud_color, (int(x - size*0.3), int(y - size*0.5)), int(size*0.6))

def run_menu():
    global WIN
    WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    pygame.display.set_caption("Flappy Bird Menu")
    
    clock = pygame.time.Clock()
    title_font = pygame.font.Font(None, 80)
    subtitle_font = pygame.font.Font(None, 32)
    background_elements = create_background_elements()

    current_user = None

    buttons = []
    button_y_start = 320
    buttons.append(Button((WIN_WIDTH - BUTTON_WIDTH) // 2, button_y_start, BUTTON_WIDTH, BUTTON_HEIGHT, "Play Single Player", 32))
    buttons.append(Button((WIN_WIDTH - BUTTON_WIDTH) // 2, button_y_start + BUTTON_HEIGHT + BUTTON_MARGIN, BUTTON_WIDTH, BUTTON_HEIGHT, "AI with Moving Pipes", 28))
    buttons.append(Button((WIN_WIDTH - BUTTON_WIDTH) // 2, button_y_start + 2 * (BUTTON_HEIGHT + BUTTON_MARGIN), BUTTON_WIDTH, BUTTON_HEIGHT, "AI with Levels", 32))
    buttons.append(Button((WIN_WIDTH - BUTTON_WIDTH) // 2, button_y_start + 3 * (BUTTON_HEIGHT + BUTTON_MARGIN), BUTTON_WIDTH, BUTTON_HEIGHT, "Man VS The Machine", 32))
    buttons.append(Button((WIN_WIDTH - BUTTON_WIDTH) // 2, button_y_start + 4 * (BUTTON_HEIGHT + BUTTON_MARGIN), BUTTON_WIDTH, BUTTON_HEIGHT, "Register", 32))
    buttons.append(Button((WIN_WIDTH - BUTTON_WIDTH) // 2, button_y_start + 5 * (BUTTON_HEIGHT + BUTTON_MARGIN), BUTTON_WIDTH, BUTTON_HEIGHT, "Login", 32))
    buttons.append(Button((WIN_WIDTH - BUTTON_WIDTH) // 2, button_y_start + 6 * (BUTTON_HEIGHT + BUTTON_MARGIN), BUTTON_WIDTH, BUTTON_HEIGHT, "Exit Game", 32))
    buttons[5].text = "Logout" if current_user else "Login"

    title_bounce = 0
    subtitle_fade = 0
    last_time = pygame.time.get_ticks()

    running = True
    while running:
        current_time = pygame.time.get_ticks()
        dt = (current_time - last_time) / 1000.0
        last_time = current_time

        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_click = True
            if event.type == pygame.USEREVENT + 1:
                for button in buttons:
                    button.is_clicked_state = False

        title_bounce += dt * 2
        subtitle_fade += dt * 1.5
        
        for element in background_elements:
            element.update(dt)
        
        WIN.blit(BG_IMG, (0, 0))
        for element in background_elements:
            if element.image is None:
                draw_cloud(WIN, element.x, element.y, 25)
            else:
                WIN.blit(element.image, (element.x, element.y))
        
        overlay = pygame.Surface((WIN_WIDTH, WIN_HEIGHT))
        overlay.set_alpha(30)
        overlay.fill((0, 0, 0))
        WIN.blit(overlay, (0, 0))
        
        title_y = 120 + math.sin(title_bounce) * 5
        render_outlined_text(WIN, "Flappy Bird", title_font, (WIN_WIDTH // 2, title_y),
                             SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL)
        
        subtitle_alpha = int(128 + 127 * math.sin(subtitle_fade))
        subtitle_text = subtitle_font.render("Choose Your Adventure!", True, (255, 255, 255))
        subtitle_rect = subtitle_text.get_rect(center=(WIN_WIDTH // 2, 200))
        subtitle_surface = pygame.Surface(subtitle_text.get_size(), pygame.SRCALPHA)
        subtitle_surface.blit(subtitle_text, (0, 0))
        subtitle_surface.set_alpha(subtitle_alpha)
        WIN.blit(subtitle_surface, subtitle_rect)
        
        # ----- Center buttons -----
        for i, button in enumerate(buttons):
            button.check_hover(mouse_pos)
            button.update(dt)
            button.draw(WIN)
            
            if button.is_clicked(mouse_pos, mouse_click):
                if i == 0:
                    import scripts.human_play as human_play
                    best_override = None
                    if current_user and current_user.get("username"):
                        try:
                            server_best = fetch_user_best(current_user["username"])
                            if server_best is not None:
                                best_override = server_best
                        except Exception:
                            best_override = None

                    final_score = human_play.main(best_override)
                    try:
                        player_name = (current_user or {}).get("username") or "Player"
                        new_row_id, _ = submit_score(player_name, int(final_score or 0))
                    except Exception:
                        new_row_id = None
                    # transfer to leaderboard "page"
                    run_leaderboard_screen(highlight_id=new_row_id)
                    continue
                elif i == 1:
                    from ..ai import multi_generation
                    multi_generation.run_moving(os.path.join(os.path.dirname(__file__), "..", "..", "configs", "config-feedforward.txt"))
                    return
                elif i == 2:
                    from ..ai import multi_generation
                    multi_generation.run_levels(os.path.join(os.path.dirname(__file__), "..", "..", "configs", "config-feedforward.txt"))
                    return
                elif i == 3:
                    import scripts.man_vs_machine as man_vs_machine
                    man_vs_machine.main()
                    return
                elif i == 4:
                    result = run_registration()
                    if result:
                        username, pwd = result
                        ok, msg = register_user_to_mongo(username, pwd)
                        print("Registration:", msg)
                elif i == 5:
                    if current_user:
                        current_user = None
                        buttons[5].text = "Login"
                        print("Logged out.")
                    else:
                        user = run_login()
                        if user:
                            current_user = user
                            buttons[5].text = "Logout"
                            print("Logged in as:", current_user.get("username"))
                elif i == 6:
                    pygame.quit()
                    sys.exit()

        # ----- Chips -----
        user_label = current_user.get("username") if current_user else None
        user_chip_rect = draw_user_chip(WIN, user_label)
        lb_chip_rect = draw_leaderboard_chip(WIN)
        # Position host/join chips stacked below leaderboard
        next_y = lb_chip_rect.bottom + 8
        host_chip_rect = draw_host_chip(WIN, next_y)
        join_chip_rect = draw_join_chip(WIN, host_chip_rect.bottom + 8)

        # user chip
        if mouse_click and user_chip_rect.collidepoint(mouse_pos):
            if current_user:
                current_user = None
                buttons[5].text = "Login"
                print("Logged out.")
            else:
                u = run_login()
                if u:
                    current_user = u
                    buttons[5].text = "Logout"
                    print("Logged in as:", current_user.get("username"))

        # leaderboard chip -> transfer to leaderboard "page"
        if mouse_click and lb_chip_rect.collidepoint(mouse_pos):
            run_leaderboard_screen()

        # Host chip -> run host with defaults (NO prompts)
        if mouse_click and host_chip_rect.collidepoint(mouse_pos):
            try:
                from ..multiplayer import online_two_player_host as host_mod
                host_mod.main()  # same as: python online_two_player_host.py
            except Exception as e:
                print("Failed to start host:", e)
            continue

        # Join chip -> just launch client; the client will ask for the IP
        if mouse_click and join_chip_rect.collidepoint(mouse_pos):
            try:
                from ..multiplayer import online_two_player_client as cli_mod
                cli_mod.main()  # client shows its own IP prompt
            except Exception as e:
                print("Failed to join:", e)
            continue

        pygame.display.update()
        clock.tick(60)

if __name__ == "__main__":
    run_menu()
