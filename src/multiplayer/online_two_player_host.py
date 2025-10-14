import pygame
import time
import random
import socket
from typing import List, Set
import socket as _sock

from ..core.assets import (
    BG_IMG,
    GAMEOVER_IMG,
    SCORE_FONT,
    FINAL_SCORE_FONT,
    SCORE_FILL,
    SCORE_OUTLINE,
)
from ..core.pipe import Pipe
from ..core.bird import Bird
from ..ui.button import render_outlined_text
from ..ai.net import make_server, send_json, start_reader

WIN_WIDTH = 800
WIN_HEIGHT = 900
FPS = 60

# -------- Colors --------
P1_COLOR = (255, 80, 80)   # red
P2_COLOR = (0, 200, 255)   # cyan
TAG_COLOR = (240, 240, 240)

def _get_local_ips():
    """Collect likely LAN IPs to show on the waiting screen / console."""
    ips = set()
    try:
        s = _sock.socket(_sock.AF_INET, _sock.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    try:
        for ip in _sock.gethostbyname_ex(_sock.gethostname())[2]:
            if ip.startswith(("10.", "172.", "192.168.")):
                ips.add(ip)
    except Exception:
        pass
    return sorted(ips)

def main(host="0.0.0.0", port=50007):
    pygame.init()
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    pygame.display.set_caption("Flappy Bird - LAN Host (Player 1)")
    clock = pygame.time.Clock()
    BG = pygame.transform.scale(BG_IMG, (WIN_WIDTH, WIN_HEIGHT))
    HUD_FONT = pygame.font.Font(None, 28)

    # --- Networking (non-blocking accept) ---
    print(f"[HOST] Listening on {host}:{port} ...")
    for ip in _get_local_ips():
        print(f"[HOST] Connect clients to: {ip}:{port}")
    server = make_server(host, port)
    server.settimeout(0.1)
    conn = None
    reader_started = False
    remote_flap = False

    def on_msg(msg: dict):
        nonlocal remote_flap
        if msg.get("type") == "input" and msg.get("action") == "flap":
            remote_flap = True
        # you could handle other client messages here if needed

    # --- World (single-player mechanics, duplicated for 2 birds) ---
    def reset_game():
        nonlocal bird1, bird2, pipes, score1, score2, game_over1, game_over2, passed_p1, passed_p2
        bird1 = Bird(300, 400, "human")  # host (red)
        bird2 = Bird(300, 500, "ai")     # client (cyan)
        bird2.x = bird1.x - 100
        pipes = [Pipe(800)]
        score1 = 0
        score2 = 0
        game_over1 = False
        game_over2 = False
        passed_p1 = set()  # type: Set[Pipe]
        passed_p2 = set()  # type: Set[Pipe]

    bird1 = bird2 = None
    pipes: List[Pipe] = []
    passed_p1: Set[Pipe] = set()
    passed_p2: Set[Pipe] = set()
    score1 = score2 = 0
    game_over1 = game_over2 = False
    reset_game()

    last_state_sent = 0.0
    SEND_HZ = 30
    dots = 0

    def send_state():
        if not conn:
            return
        state = {
            "type": "state",
            "p1": {"x": bird1.x, "y": bird1.y, "tilt": bird1.tilt, "alive": not game_over1, "score": score1},
            "p2": {"x": bird2.x, "y": bird2.y, "tilt": bird2.tilt, "alive": not game_over2, "score": score2},
            "pipes": [{"x": p.x, "top": p.top, "bottom": p.bottom} for p in pipes],
            "game_over1": game_over1,
            "game_over2": game_over2,
            "w": WIN_WIDTH, "h": WIN_HEIGHT,
        }
        send_json(conn, state)

    def tell_client_close():
        try:
            if conn:
                send_json(conn, {"type": "close"})
        except Exception:
            pass

    run = True
    while run:
        clock.tick(FPS)

        # Accept client without freezing
        if not conn:
            try:
                conn, addr = server.accept()
                print(f"[HOST] Client connected from {addr}")
            except socket.timeout:
                pass
            except OSError:
                pass

        # Start reader thread once
        if conn and not reader_started:
            start_reader(conn, on_msg)
            reader_started = True

        # Host input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # back to menu via window X
                tell_client_close()
                run = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    # back to menu via M (no pygame.quit here!)
                    tell_client_close()
                    run = False
                elif event.key == pygame.K_SPACE and not game_over1:
                    bird1.jump()
                elif event.key == pygame.K_r and (game_over1 and game_over2):
                    reset_game()

        # Waiting screen until client connects
        if not conn and run:
            win.blit(BG, (0, 0))
            msg = "Waiting for client" + "." * ((dots // 20) % 4)
            dots += 1
            render_outlined_text(
                win, msg, SCORE_FONT, (WIN_WIDTH // 2, WIN_HEIGHT // 2 - 60),
                SCORE_FILL, SCORE_OUTLINE, SCORE_FILL
            )
            render_outlined_text(
                win, "Press M for menu", HUD_FONT, (WIN_WIDTH // 2, WIN_HEIGHT // 2 - 20),
                (240, 240, 240), SCORE_OUTLINE, SCORE_FILL
            )
            y = WIN_HEIGHT // 2 + 10
            for ip in _get_local_ips():
                render_outlined_text(
                    win, f"Connect to: {ip}:{port}", HUD_FONT, (WIN_WIDTH // 2, y),
                    (240, 240, 240), SCORE_OUTLINE, SCORE_FILL
                )
                y += 28
            pygame.display.update()
            continue

        if not run:
            break

        # Apply client flap
        if remote_flap and not game_over2:
            bird2.jump()
        remote_flap = False

        # ---- Game step (same as single-player, per bird) ----
        if not (game_over1 and game_over2):
            if not game_over1:
                bird1.move()
            if not game_over2:
                bird2.move()

            remove = []
            for pipe in pipes:
                pipe.move()

                # Collisions
                if not game_over1 and pipe.collide(bird1):
                    game_over1 = True
                if not game_over2 and pipe.collide(bird2):
                    game_over2 = True

                # Bounds
                if not game_over1 and (bird1.y > WIN_HEIGHT or bird1.y < 0):
                    game_over1 = True
                if not game_over2 and (bird2.y > WIN_HEIGHT or bird2.y < 0):
                    game_over2 = True

                # Independent scoring (only while that player is alive)
                if (not game_over1) and (pipe.x + pipe.PIPE_TOP.get_width() < bird1.x) and (pipe not in passed_p1):
                    score1 += 1
                    passed_p1.add(pipe)
                if (not game_over2) and (pipe.x + pipe.PIPE_TOP.get_width() < bird2.x) and (pipe not in passed_p2):
                    score2 += 1
                    passed_p2.add(pipe)

                # Remove off-screen
                if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                    remove.append(pipe)

            for r in remove:
                passed_p1.discard(r)
                passed_p2.discard(r)
                pipes.remove(r)

            if pipes and pipes[-1].x < 450:
                pipes.append(Pipe(WIN_WIDTH))

        # ---- Draw ----
        win.blit(BG, (0, 0))
        for pipe in pipes:
            pipe.draw(win)
        # Draw birds ONLY if alive (vanish on death)
        if not game_over1:
            bird1.draw(win)
        if not game_over2:
            bird2.draw(win)

        # Small side HUD scores
        render_outlined_text(win, f"You: {score1}", HUD_FONT, (70, 30),
                             P1_COLOR, SCORE_OUTLINE, SCORE_FILL)
        render_outlined_text(win, f"P2: {score2}", HUD_FONT, (WIN_WIDTH - 70, 30),
                             P2_COLOR, SCORE_OUTLINE, SCORE_FILL)

        # Small OUT tag if one player is out
        if game_over1 ^ game_over2:
            if game_over1:
                render_outlined_text(win, "You OUT", HUD_FONT, (70, 60),
                                     TAG_COLOR, SCORE_OUTLINE, SCORE_FILL)
            if game_over2:
                render_outlined_text(win, "P2 OUT", HUD_FONT, (WIN_WIDTH - 70, 60),
                                     TAG_COLOR, SCORE_OUTLINE, SCORE_FILL)

        # Final banner when both are out (WIN / LOSE / DRAW)
        if game_over1 and game_over2:
            if score1 > score2:
                result = "YOU WIN!"
            elif score2 > score1:
                result = "YOU LOSE!"
            else:
                result = "DRAW!"

            render_outlined_text(win, result, FINAL_SCORE_FONT,
                                 (WIN_WIDTH // 2, WIN_HEIGHT // 2 - 40),
                                 SCORE_FILL, SCORE_OUTLINE, SCORE_FILL)
            render_outlined_text(win, f"You: {score1}   P2: {score2}", FINAL_SCORE_FONT,
                                 (WIN_WIDTH // 2, WIN_HEIGHT // 2 + 20),
                                 SCORE_FILL, SCORE_OUTLINE, SCORE_FILL)
            render_outlined_text(win, "Press R to restart or M for menu", HUD_FONT,
                                 (WIN_WIDTH // 2, WIN_HEIGHT // 2 + 90),
                                 SCORE_FILL, SCORE_OUTLINE, SCORE_FILL)

        pygame.display.update()

        # Send state ~30 Hz
        now = time.time()
        if now - last_state_sent >= 1.0 / SEND_HZ:
            send_state()
            last_state_sent = now

    # ---- Cleanup (do NOT pygame.quit — we return to menu) ----
    try:
        if conn:
            tell_client_close()
            conn.close()
    except Exception:
        pass
    server.close()
    # Just return to the caller (menu)
    return

if __name__ == "__main__":
    main()
