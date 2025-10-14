# online_two_player_client.py
import pygame
from ..core.assets import (
    BG_IMG, SCORE_FONT, FINAL_SCORE_FONT, SCORE_FILL, SCORE_OUTLINE,
    PIPE_IMG, GAMEOVER_IMG
)
from ..ui.button import render_outlined_text
from ..core.bird import Bird
from ..ai.net import connect, send_json, start_reader

# -------- Window --------
WIN_WIDTH = 800
WIN_HEIGHT = 900
FPS = 60

PIPE_TOP_IMG = pygame.transform.flip(PIPE_IMG, False, True)
PIPE_BOTTOM_IMG = PIPE_IMG

P1_COLOR = (255, 80, 80)
P2_COLOR = (0, 200, 255)
TAG_COLOR = (240, 240, 240)

def scaled_bg():
    return pygame.transform.scale(BG_IMG, (WIN_WIDTH, WIN_HEIGHT))

# ---------- Fancy IP Prompt ----------
def ip_prompt(surface, title="Join Host", placeholder="Type host IP (e.g., 127.0.0.1)"):
    """
    Modal IP input with a soft overlay and card UI.
    Returns the entered string, or None if ESC/M / window close.
    """
    clock = pygame.time.Clock()
    BG = scaled_bg()

    # Fonts
    title_font = pygame.font.Font(None, 48)
    label_font = pygame.font.Font(None, 26)
    input_font = pygame.font.Font(None, 28)
    hint_font  = pygame.font.Font(None, 22)

    # Card metrics
    card_w, card_h = 560, 220
    card = pygame.Rect((WIN_WIDTH - card_w)//2, (WIN_HEIGHT - card_h)//2, card_w, card_h)
    input_rect = pygame.Rect(card.x + 28, card.y + 110, card_w - 56, 42)

    text_chars = []
    cursor = True
    blink = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_m):
                    return None
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    entered = "".join(text_chars).strip()
                    return entered if entered else None
                elif event.key == pygame.K_BACKSPACE:
                    if text_chars:
                        text_chars.pop()
                else:
                    ch = event.unicode
                    if ch and 32 <= ord(ch) < 127 and len(text_chars) < 64:
                        text_chars.append(ch)

        blink = (blink + 1) % 60
        cursor = blink < 30

        # --- Draw modal ---
        surface.blit(BG, (0, 0))

        # soft dark overlay
        overlay = pygame.Surface((WIN_WIDTH, WIN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surface.blit(overlay, (0, 0))

        # card
        card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        pygame.draw.rect(card_surf, (245, 245, 245, 240), card_surf.get_rect(), border_radius=16)
        pygame.draw.rect(card_surf, (40, 40, 40, 200), card_surf.get_rect(), width=2, border_radius=16)
        surface.blit(card_surf, card.topleft)

        # title
        title_s = title_font.render(title, True, (25, 25, 25))
        surface.blit(title_s, (card.centerx - title_s.get_width()//2, card.y + 22))

        # label
        label_s = label_font.render("Host IP address", True, (70, 70, 70))
        surface.blit(label_s, (input_rect.x, input_rect.y - 28))

        # input box
        pygame.draw.rect(surface, (255, 255, 255), input_rect, border_radius=10)
        pygame.draw.rect(surface, (60, 60, 60), input_rect, width=2, border_radius=10)

        typed = "".join(text_chars)
        if typed:
            txt_surface = input_font.render(typed, True, (20, 20, 20))
        else:
            txt_surface = input_font.render(placeholder, True, (140, 140, 140))
        surface.blit(txt_surface, (input_rect.x + 12, input_rect.y + (input_rect.h - txt_surface.get_height())//2))

        # caret
        if typed and cursor:
            cx = input_rect.x + 12 + txt_surface.get_width() + 2
            cy = input_rect.y + 10
            pygame.draw.line(surface, (30, 30, 30), (cx, cy), (cx, cy + input_rect.h - 20), 2)

        # hint
        hint_s = hint_font.render("Press Enter to connect • Esc/M to cancel", True, (80, 80, 80))
        surface.blit(hint_s, (card.centerx - hint_s.get_width()//2, card.bottom - 36))

        pygame.display.update()
        clock.tick(60)

# ---------- Client Main ----------
def main(host_ip=None, port=50007):
    pygame.init()
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    pygame.display.set_caption("Flappy Bird - LAN Client (Player 2)")
    clock = pygame.time.Clock()
    BG = scaled_bg()
    HUD_FONT = pygame.font.Font(None, 28)

    # Ask for IP if not provided
    while not host_ip:
        host_ip = ip_prompt(win)
        if host_ip is None:
            return  # <- return to menu without pygame.quit()

    # Try to connect; on failure re-open prompt
    while True:
        try:
            print(f"[CLIENT] Connecting to {host_ip}:{port} ...")
            sock = connect(host_ip, port)
            break
        except OSError:
            # brief error screen, then re-prompt
            timer = 0
            while timer < 90:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return
                win.blit(BG, (0, 0))
                render_outlined_text(win, f"Could not connect to {host_ip}:{port}",
                                     SCORE_FONT, (WIN_WIDTH // 2, WIN_HEIGHT // 2 - 20),
                                     SCORE_FILL, SCORE_OUTLINE, SCORE_FILL)
                render_outlined_text(win, "Press any key to retry • Esc/M to quit",
                                     SCORE_FONT, (WIN_WIDTH // 2, WIN_HEIGHT // 2 + 30),
                                     SCORE_FILL, SCORE_OUTLINE, SCORE_FILL)
                pygame.display.update()
                clock.tick(60)
                timer += 1

            # wait for key then either quit on Esc/M or retry
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_ESCAPE, pygame.K_m):
                            return
                        waiting = False
                clock.tick(60)

            host_ip = None
            continue

    # Visual birds (server is authoritative)
    host_bird   = Bird(300, 400, "human")  # P1 red
    client_bird = Bird(300, 500, "ai")     # P2 cyan

    class RemoteState:
        p1 = {"x": 300, "y": 400, "tilt": 0, "alive": True, "score": 0}
        p2 = {"x": 300, "y": 500, "tilt": 0, "alive": True, "score": 0}
        pipes = []   # [{"x","top","bottom"}, ...]
        game_over1 = False
        game_over2 = False
        close = False
    state = RemoteState()

    def on_msg(msg: dict):
        # host → client updates
        if msg.get("type") == "state":
            state.p1 = msg.get("p1", state.p1)
            state.p2 = msg.get("p2", state.p2)
            state.pipes = msg.get("pipes", state.pipes)
            state.game_over1 = msg.get("game_over1", state.game_over1)
            state.game_over2 = msg.get("game_over2", state.game_over2)

            host_bird.x = state.p1.get("x", host_bird.x)
            host_bird.y = state.p1.get("y", host_bird.y)
            host_bird.tilt = state.p1.get("tilt", host_bird.tilt)
            host_bird.jump_frame = 0

            client_bird.x = state.p2.get("x", client_bird.x)
            client_bird.y = state.p2.get("y", client_bird.y)
            client_bird.tilt = state.p2.get("tilt", client_bird.tilt)
            client_bird.jump_frame = 0

        elif msg.get("type") == "close":
            state.close = True  # host backed out

    start_reader(sock, on_msg)

    # --- Game loop ---
    run = True
    while run:
        clock.tick(FPS)

        # leave cleanly if host closed
        if state.close:
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    try:
                        send_json(sock, {"type": "input", "action": "flap"})
                    except OSError:
                        pass
                elif event.key in (pygame.K_ESCAPE, pygame.K_m):
                    run = False

        # Draw bg
        win.blit(BG, (0, 0))

        # Pipes from server (top & bottom)
        for p in state.pipes:
            x = int(p["x"])
            top_y = int(p["top"])
            bottom_y = int(p["bottom"])
            win.blit(PIPE_TOP_IMG, (x, top_y))
            win.blit(PIPE_BOTTOM_IMG, (x, bottom_y))

        # Draw birds only while alive (vanish on death)
        if state.p1.get("alive", True):
            host_bird.draw(win)
        if state.p2.get("alive", True):
            client_bird.draw(win)

        # HUD scores (small, sides)
        render_outlined_text(
            win, f"P1: {state.p1.get('score', 0)}",
            HUD_FONT, (70, 30), P1_COLOR, SCORE_OUTLINE, SCORE_FILL
        )
        render_outlined_text(
            win, f"You: {state.p2.get('score', 0)}",
            HUD_FONT, (WIN_WIDTH - 70, 30), P2_COLOR, SCORE_OUTLINE, SCORE_FILL
        )

        # Out markers
        if state.game_over1 ^ state.game_over2:
            if state.game_over1:
                render_outlined_text(win, "P1 OUT", HUD_FONT, (70, 60),
                                     TAG_COLOR, SCORE_OUTLINE, SCORE_FILL)
            if state.game_over2:
                render_outlined_text(win, "YOU ARE OUT", HUD_FONT, (WIN_WIDTH - 110, 60),
                                     TAG_COLOR, SCORE_OUTLINE, SCORE_FILL)

        # Final result when both are out
        if state.game_over1 and state.game_over2:
            s1 = state.p1.get("score", 0)
            s2 = state.p2.get("score", 0)
            if s2 > s1:
                result = "YOU WIN!"
            elif s1 > s2:
                result = "YOU LOSE!"
            else:
                result = "DRAW!"

            render_outlined_text(
                win, result, FINAL_SCORE_FONT,
                (WIN_WIDTH // 2, WIN_HEIGHT // 2 - 40),
                SCORE_FILL, SCORE_OUTLINE, SCORE_FILL
            )
            render_outlined_text(
                win, f"P1: {s1}   You: {s2}", FINAL_SCORE_FONT,
                (WIN_WIDTH // 2, WIN_HEIGHT // 2 + 20),
                SCORE_FILL, SCORE_OUTLINE, SCORE_FILL
            )

        pygame.display.update()

    # Cleanup & return to menu (do NOT pygame.quit() here)
    try:
        sock.close()
    except Exception:
        pass
    return  # hand control back to menu.py without tearing down pygame

if __name__ == "__main__":
    # Running directly still shows the nice IP prompt first
    main()
