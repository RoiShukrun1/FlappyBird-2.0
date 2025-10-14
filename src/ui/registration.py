# registration.py
import pygame
from typing import Optional, Tuple
import os
import requests

from ..core.assets import BG_IMG, SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL
from .button import Button, render_outlined_text

API_BASE = "http://127.0.0.1:8001"
# -----------------------------
# Small InputBox component
# -----------------------------
class InputBox:
    def __init__(self, x: int, y: int, w: int, h: int, font: pygame.font.Font, placeholder: str = "",
                 is_password: bool = False, max_len: int = 128):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.placeholder = placeholder
        self.is_password = is_password
        self.max_len = max_len
        self.text = ""
        self.active = False
        self.blink = 0.0

        self.border_color_inactive = (180, 180, 200)
        self.border_color_active = (255, 200, 80)
        self.fill_color = (15, 15, 20, 200)
        self.text_color = (245, 245, 245)
        self.placeholder_color = (170, 170, 180)

        self.pad_x = 12
        self.pad_y = 8

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
        if not self.active:
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_TAB):
                pass
            else:
                if len(self.text) < self.max_len and event.unicode and event.unicode.isprintable():
                    self.text += event.unicode

    def update(self, dt: float):
        self.blink += dt

    def draw(self, surface: pygame.Surface):
        box_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(box_surface, self.fill_color, box_surface.get_rect(), border_radius=10)
        border_col = self.border_color_active if self.active else self.border_color_inactive
        pygame.draw.rect(box_surface, border_col, box_surface.get_rect(), width=2, border_radius=10)

        if self.text:
            display_text = ("•" * len(self.text)) if self.is_password else self.text
            txt_surf = self.font.render(display_text, True, self.text_color)
        else:
            txt_surf = self.font.render(self.placeholder, True, self.placeholder_color)

        box_surface.blit(txt_surf, (self.pad_x, self.pad_y))

        if self.active and (int(self.blink * 2) % 2 == 0):
            cursor_x = self.pad_x + txt_surf.get_width() + 2
            cursor_y = self.pad_y + 2
            pygame.draw.rect(box_surface, self.text_color, (cursor_x, cursor_y, 2, self.font.get_height() - 4))
        surface.blit(box_surface, self.rect.topleft)

# -----------------------------
# Helpers
# -----------------------------
def _validate(username: str, password: str) -> Optional[str]:
    # No username validation (as requested)
    if not password or len(password) < 6:
        return "Password must be at least 6 characters."
    return None

# -----------------------------
# UI
# -----------------------------
def run_registration() -> Optional[Tuple[str, str]]:
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((800, 900))
    win_w, win_h = screen.get_size()

    pygame.display.set_caption("Create Your Player")

    clock = pygame.time.Clock()
    title_font = pygame.font.Font(None, 80)
    label_font = pygame.font.Font(None, 36)
    input_font = pygame.font.Font(None, 40)
    hint_font = pygame.font.Font(None, 28)

    form_w = 520
    form_x = (win_w - form_w) // 2
    form_y = 240
    row_h = 80

    username_box = InputBox(form_x, form_y + row_h * 0,   form_w, 56, input_font, "Username")
    pass_box     = InputBox(form_x, form_y + row_h * 1.5, form_w, 56, input_font, "Password", is_password=True)

    btn_w, btn_h = 200, 60
    btn_gap = 24
    btn_y = form_y + row_h * 2 + 40
    submit_btn = Button(form_x, btn_y, btn_w, btn_h, "Submit", 32)
    cancel_btn = Button(form_x + btn_w + btn_gap, btn_y, btn_w, btn_h, "Cancel", 32)
    toggle_btn = Button(form_x + (form_w - 50), pass_box.rect.bottom + 12, 150, 40, "Show Password", 24)

    error_msg = ""
    last = pygame.time.get_ticks()
    username_box.active = True

    while True:
        now = pygame.time.get_ticks()
        dt = (now - last) / 1000.0
        last = now

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key == pygame.K_TAB:
                    username_box.active, pass_box.active = (False, True) if username_box.active else (True, False)
                if event.key == pygame.K_RETURN:
                    username = username_box.text.strip()
                    pwd = pass_box.text
                    err = _validate(username, pwd)
                    if err: error_msg = err
                    else: return (username, pwd)

            username_box.handle_event(event)
            pass_box.handle_event(event)

        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()[0]

        for b in (submit_btn, cancel_btn, toggle_btn):
            b.check_hover(mouse)
            b.update(dt)

        if submit_btn.is_clicked(mouse, click):
            username = username_box.text.strip()
            pwd = pass_box.text
            err = _validate(username, pwd)
            if err: error_msg = err
            else: return (username, pwd)

        if cancel_btn.is_clicked(mouse, click):
            return None

        if toggle_btn.is_clicked(mouse, click):
            pass_box.is_password = not pass_box.is_password
            toggle_btn.text = "Hide Password" if not pass_box.is_password else "Show Password"

        # Draw
        screen.blit(BG_IMG, (0, 0))
        overlay = pygame.Surface((win_w, win_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 90))
        screen.blit(overlay, (0, 0))

        render_outlined_text(screen, "Create Your Player", title_font, (win_w // 2, 120),
                             SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL)

        sub = hint_font.render("Pick a username and a password.", True, (235, 235, 240))
        screen.blit(sub, sub.get_rect(center=(win_w // 2, 168)))

        user_lbl = label_font.render("Username", True, (240, 240, 245))
        pass_lbl = label_font.render("Password", True, (240, 240, 245))
        screen.blit(user_lbl, (form_x, username_box.rect.top - 36))
        screen.blit(pass_lbl, (form_x, pass_box.rect.top - 36))

        username_box.update(dt); pass_box.update(dt)
        username_box.draw(screen); pass_box.draw(screen)

        submit_btn.draw(screen); cancel_btn.draw(screen); toggle_btn.draw(screen)

        if error_msg:
            err_surf = hint_font.render(error_msg, True, (255, 110, 110))
            screen.blit(err_surf, (form_x, btn_y + btn_h + 16))

        pygame.display.flip()
        clock.tick(60)

# -----------------------------
# API call (keeps old name so menu import stays the same)
# -----------------------------
def register_user_to_mongo(username: str, password: str) -> tuple[bool, str]:
    """Call the server to register."""
    try:
        r = requests.post(f"{API_BASE}/register",
                          json={"username": username, "password": password},
                          timeout=4)
        if r.status_code == 200:
            return True, "Registered successfully."
        # try to read error message
        try:
            msg = r.json().get("detail", "Registration failed.")
        except Exception:
            msg = r.text or "Registration failed."
        return False, msg
    except Exception as e:
        return False, f"Network error: {e}"

if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((800, 900))
    res = run_registration()
    print("Result:", res)
