# leaderboard_client.py
import os
from typing import Dict, List, Optional, Tuple
import requests

# --- HTTP client config ---
API_BASE = os.getenv("LB_API_BASE", "http://127.0.0.1:8001")  # point this to your server
TIMEOUT = float(os.getenv("LB_TIMEOUT", "2.0"))

# POST  /leaderboard/submit  body: {"name": str, "score": int}
#      -> {"ok": true, "id": "abc123", "rank": 7}
# GET   /leaderboard/top?limit=10
#      -> {"ok": true, "items": [{"id": "abc123", "name": "Kobi", "score": 42, "rank": 1}, ...]}
# GET   /user/best?username=Kobi
#      -> {"ok": true, "best": 123}

def submit_score(name: str, score: int) -> Tuple[Optional[str], Optional[int]]:
    try:
        r = requests.post(
            f"{API_BASE}/leaderboard/submit",
            json={"name": name, "score": int(score)},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("ok"):
            return data.get("id"), data.get("rank")
    except Exception:
        pass
    return None, None


def fetch_top10(limit: int = 10) -> List[Dict]:
    try:
        r = requests.get(f"{API_BASE}/leaderboard/top", params={"limit": limit}, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if data.get("ok") and isinstance(data.get("items"), list):
            out = []
            for i, it in enumerate(data["items"][:limit]):
                out.append({
                    "id": it.get("id") or f"row_{i}",
                    "name": it.get("name") or "Anonymous",
                    "score": int(it.get("score", 0)),
                    "rank": int(it.get("rank", i + 1)) if "rank" in it else i + 1,
                })
            return out
    except Exception:
        pass
    return []


def fetch_user_best(username: str) -> Optional[int]:
    """Return user's best score from server, or None on failure."""
    try:
        r = requests.get(f"{API_BASE}/user/best", params={"username": username}, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if data.get("ok"):
            return int(data.get("best", 0))
    except Exception:
        pass
    return None


# ============================
# UI "page" (dedicated screen)
# ============================

# NOTE: kept here per request so the menu can "transfer" to this page.
import pygame
from ..core.assets import BG_IMG, SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL
from ..ui.button import Button, render_outlined_text

WIN_WIDTH = 800
WIN_HEIGHT = 900

def _draw_leaderboard_panel(surface, items, my_id=None, base_y=200):
    """Transparent card with NAME | SCORE, optional highlight for my_id."""
    import time as _time, math as _math

    panel_w, panel_h = 560, 480
    panel_x = (WIN_WIDTH - panel_w) // 2
    panel_y = base_y

    overlay = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(overlay, (0, 0, 0, 140), overlay.get_rect(), border_radius=18)
    pygame.draw.rect(overlay, (255, 255, 255, 70), overlay.get_rect(), width=2, border_radius=18)

    title_font = pygame.font.Font(None, 48)
    row_font = pygame.font.Font(None, 30)
    small_font = pygame.font.Font(None, 26)

    title = title_font.render("Leaderboard — Top 10", True, (255, 255, 255))
    overlay.blit(title, (overlay.get_width() // 2 - title.get_width() // 2, 16))

    header_y = 70
    col_name_x = 28
    col_score_x = panel_w - 110

    hdr_name = small_font.render("NAME", True, (200, 200, 200))
    hdr_score = small_font.render("SCORE", True, (200, 200, 200))
    overlay.blit(hdr_name, (col_name_x, header_y))
    overlay.blit(hdr_score, (col_score_x, header_y))

    row_y = header_y + 16
    line_h = 32
    now = _time.time()

    for i, it in enumerate(items[:10]):
        y = row_y + 8 + i * (line_h + 8)
        row_rect = pygame.Rect(14, y, panel_w - 28, line_h + 4)

        if my_id and it.get("id") == my_id:
            alpha = int(100 + 70 * (0.5 + 0.5 * _math.sin(now * 4.0)))
            glow = pygame.Surface((row_rect.width, row_rect.height), pygame.SRCALPHA)
            glow.fill((255, 200, 0, alpha))
            overlay.blit(glow, (row_rect.x, row_rect.y))

        name_txt = row_font.render(str(it.get("name", "Anonymous"))[:18], True, (240, 240, 240))
        score_txt = row_font.render(str(it.get("score", 0)), True, (240, 240, 240))
        overlay.blit(name_txt, (col_name_x, y))
        overlay.blit(score_txt, (col_score_x, y))

    surface.blit(overlay, (panel_x, panel_y))
    return pygame.Rect(panel_x, panel_y, panel_w, panel_h)


def run_leaderboard_screen(highlight_id: Optional[str] = None):
    """
    Dedicated leaderboard screen; returns to caller when Back/ESC or window close.
    """
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    pygame.display.set_caption("Flappy Bird — Leaderboard")

    clock = pygame.time.Clock()
    title_font = pygame.font.Font(None, 80)
    subtitle_font = pygame.font.Font(None, 32)

    items = fetch_top10(limit=10)

    back_btn = Button(WIN_WIDTH - 160, 24, 130, 44, "Back", 28)
    refresh_btn = Button(30, 24, 130, 44, "Refresh", 28)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_click = True

        # background
        screen = pygame.display.get_surface()
        screen.blit(BG_IMG, (0, 0))
        dark = pygame.Surface((WIN_WIDTH, WIN_HEIGHT))
        dark.set_alpha(40)
        dark.fill((0, 0, 0))
        screen.blit(dark, (0, 0))

        # header
        render_outlined_text(screen, "Flappy Bird", title_font, (WIN_WIDTH // 2, 100),
                             SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL)
        subtitle_text = subtitle_font.render("Global Leaderboard", True, (255, 255, 255))
        screen.blit(subtitle_text, subtitle_text.get_rect(center=(WIN_WIDTH // 2, 160)))

        # panel
        _draw_leaderboard_panel(screen, items, my_id=highlight_id, base_y=200)

        # buttons
        back_btn.check_hover(mouse_pos)
        back_btn.draw(screen)
        refresh_btn.check_hover(mouse_pos)
        refresh_btn.draw(screen)

        if mouse_click:
            if back_btn.is_clicked(mouse_pos, True):
                running = False
            elif refresh_btn.is_clicked(mouse_pos, True):
                items = fetch_top10(limit=10)

        pygame.display.update()
