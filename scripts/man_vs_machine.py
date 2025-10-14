import pygame
import neat
import os
import sys
import random
import math
import pickle  # <-- for loading trained birds

from src.core.bird import Bird
from src.core.pipe import Pipe
from src.core.assets import BG_IMG, SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL, GAMEOVER_IMG
from src.ui.button import Button, render_outlined_text
from src.utils.best_score import load_best_score, save_best_score

# -------------------------
# Game settings / window
# -------------------------
WIN_WIDTH = 1000
WIN_HEIGHT = 1000
UPPER_HEIGHT = WIN_HEIGHT // 2  # AI area (top half)
LOWER_HEIGHT = WIN_HEIGHT // 2  # Human area (bottom half)
FLOOR = 930
FPS = 60

pygame.init()
WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Flappy Bird - Man VS Machine")
clock = pygame.time.Clock()

# Lives system
MAX_LIVES = 3

# Pause menu settings
PAUSE_OVERLAY_COLOR = (0, 0, 0, 180)
PAUSE_BUTTON_WIDTH = 200
PAUSE_BUTTON_HEIGHT = 60
PAUSE_BUTTON_MARGIN = 20

# -------------------------
# Performance caches
# -------------------------

# Pre-cache fonts
FONT_24 = pygame.font.Font(None, 24)
FONT_28 = pygame.font.Font(None, 28)
FONT_32 = pygame.font.Font(None, 32)
FONT_36 = pygame.font.Font(None, 36)
FONT_48 = pygame.font.Font(None, 48)
FONT_72 = pygame.font.Font(None, 72)

# Pre-scale backgrounds once (convert() for fast blits)
AI_BG = pygame.transform.scale(BG_IMG.convert(), (WIN_WIDTH, UPPER_HEIGHT))
HUMAN_BG = pygame.transform.scale(BG_IMG.convert(), (WIN_WIDTH, LOWER_HEIGHT))
FULL_BG = pygame.transform.scale(BG_IMG.convert(), (WIN_WIDTH, WIN_HEIGHT))

# Reusable overlays (alpha surfaces)
OVERLAY_PAUSE = pygame.Surface((WIN_WIDTH, WIN_HEIGHT), pygame.SRCALPHA)
OVERLAY_PAUSE.fill((0, 0, 0, 120))

OVERLAY_GAMEOVER = pygame.Surface((WIN_WIDTH, WIN_HEIGHT), pygame.SRCALPHA)
OVERLAY_GAMEOVER.fill((0, 0, 0, 150))

OVERLAY_AI_DEAD = pygame.Surface((WIN_WIDTH, UPPER_HEIGHT), pygame.SRCALPHA)
OVERLAY_AI_DEAD.fill((255, 0, 0, 100))

OVERLAY_HUMAN_DEAD = pygame.Surface((WIN_WIDTH, LOWER_HEIGHT), pygame.SRCALPHA)
OVERLAY_HUMAN_DEAD.fill((255, 0, 0, 100))

# Since upper/lower halves are exactly half the window height,
# the sprite scale factor is constant 0.5 for both halves.
HALF_RATIO = 0.5

# -------------------------
# Difficulty → config mapping
# (filenames match your spelling exactly)
# -------------------------
DIFFICULTY_TO_CONFIG = {
    "Easy":    "config-feedforwardEasy.txt",
    "Meduim":  "config-feedforwardMEDIUM.txt",   # intentional spelling
    "Hard":    "config-feedforwardHard.txt",
    "Exterme": "config-feedforwardExterme.txt",  # intentional spelling
}

DIFF_DESCRIPTIONS = {
    "Easy":    "For beginners.",
    "Meduim":  "For regular players.",
    "Hard":    "For experienced players.",
    "Exterme": "For masochists.",
}

# Winner files (must exist). Uppercase names as requested.
DIFF_TO_WINNER = {
    "Easy":    "winner_EASY.pkl",
    "Meduim":  "winner_MEDUIM.pkl",
    "Hard":    "winner_HARD.pkl",
    "Exterme": "winner_EXTREME.pkl",
}

def ensure_pipe_scaled(pipe):
    """Attach half-height scaled sprites to a Pipe once (for both halves)."""
    if not hasattr(pipe, "_scaled_cached"):
        pipe.PIPE_TOP_UPPER = pygame.transform.scale(
            pipe.PIPE_TOP, (pipe.PIPE_TOP.get_width(), max(1, pipe.PIPE_TOP.get_height() // 2))
        )
        pipe.PIPE_BOTTOM_UPPER = pygame.transform.scale(
            pipe.PIPE_BOTTOM, (pipe.PIPE_BOTTOM.get_width(), max(1, pipe.PIPE_BOTTOM.get_height() // 2))
        )
        # same scale for lower half (identical size)
        pipe.PIPE_TOP_LOWER = pipe.PIPE_TOP_UPPER
        pipe.PIPE_BOTTOM_LOWER = pipe.PIPE_BOTTOM_UPPER
        pipe._scaled_cached = True

# -------------------------
# UI helpers
# -------------------------

def draw_divider_line(surface):
    """Draw a line dividing the AI and human areas."""
    pygame.draw.line(surface, SCORE_ORANGE, (0, UPPER_HEIGHT), (WIN_WIDTH, UPPER_HEIGHT), 3)

def draw_pause_menu(surface):
    """Draw pause menu overlay (reuses cached bg + overlay)."""
    surface.blit(FULL_BG, (0, 0))
    surface.blit(OVERLAY_PAUSE, (0, 0))

    render_outlined_text(
        surface,
        "PAUSED",
        FONT_72,
        (WIN_WIDTH // 2, WIN_HEIGHT // 3),
        SCORE_ORANGE,
        SCORE_OUTLINE,
        SCORE_FILL
    )

    resume_button = Button(
        (WIN_WIDTH - PAUSE_BUTTON_WIDTH) // 2,
        WIN_HEIGHT // 2 - PAUSE_BUTTON_HEIGHT - PAUSE_BUTTON_MARGIN,
        PAUSE_BUTTON_WIDTH,
        PAUSE_BUTTON_HEIGHT,
        "Resume"
    )

    restart_button = Button(
        (WIN_WIDTH - PAUSE_BUTTON_WIDTH) // 2,
        WIN_HEIGHT // 2,
        PAUSE_BUTTON_WIDTH,
        PAUSE_BUTTON_HEIGHT,
        "Restart Game"
    )

    menu_button = Button(
        (WIN_WIDTH - PAUSE_BUTTON_WIDTH) // 2,
        WIN_HEIGHT // 2 + PAUSE_BUTTON_HEIGHT + PAUSE_BUTTON_MARGIN,
        PAUSE_BUTTON_WIDTH,
        PAUSE_BUTTON_HEIGHT,
        "Main Menu"
    )

    mouse_pos = pygame.mouse.get_pos()

    for b in (resume_button, restart_button, menu_button):
        b.check_hover(mouse_pos)
        b.draw(surface)

    pygame.display.update()
    return resume_button, restart_button, menu_button

def draw_game_over_screen(surface, ai_score, human_score, ai_lives, human_lives):
    """Draw game over screen with winner announcement (cached bg+overlay)."""
    surface.blit(FULL_BG, (0, 0))
    surface.blit(OVERLAY_GAMEOVER, (0, 0))

    # Determine winner
    if ai_score > human_score:
        winner_text = "MACHINE WINS!"
    elif human_score > ai_score:
        winner_text = "HUMAN WINS!"
    else:
        winner_text = "IT'S A TIE!"

    render_outlined_text(surface, winner_text, FONT_72, (WIN_WIDTH // 2, WIN_HEIGHT // 3),
                         SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL)

    render_outlined_text(surface, f"Machine Score: {ai_score}", FONT_48, (WIN_WIDTH // 2, WIN_HEIGHT // 2),
                         SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL)
    render_outlined_text(surface, f"Human Score: {human_score}", FONT_48, (WIN_WIDTH // 2, WIN_HEIGHT // 2 + 50),
                         SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL)

    render_outlined_text(surface, "Press R to restart or M for menu", FONT_36,
                         (WIN_WIDTH // 2, WIN_HEIGHT - 100), SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL)

    pygame.display.update()

# -------------------------
# Difficulty screen
# -------------------------

def _card(surface, rect, title, subtitle, hovered):
    # Card base
    bg = (22, 22, 24)
    border = SCORE_ORANGE if hovered else (70, 70, 75)
    pygame.draw.rect(surface, bg, rect, border_radius=20)
    pygame.draw.rect(surface, border, rect, width=3, border_radius=20)

    # Title
    render_outlined_text(surface, title, FONT_48, (rect.centerx, rect.y + 36),
                         SCORE_ORANGE if hovered else (235, 235, 235),
                         SCORE_OUTLINE, SCORE_FILL)

    # Subtitle (wrap lightly)
    sub_lines = _wrap_text(subtitle, FONT_28, rect.width - 40)
    y = rect.y + 80
    for line in sub_lines[:3]:
        text_surf = FONT_28.render(line, True, (210, 210, 210))
        surface.blit(text_surf, (rect.x + 20, y))
        y += 32

def _wrap_text(text, font, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if font.size(test)[0] <= max_width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def select_difficulty_screen():
    """Returns chosen difficulty string (Easy / Meduim / Hard / Exterme)."""
    # Layout
    card_w, card_h = 360, 180
    gap_x, gap_y = 40, 30
    total_w = card_w * 2 + gap_x
    total_h = card_h * 2 + gap_y
    start_x = (WIN_WIDTH - total_w) // 2
    start_y = (WIN_HEIGHT - total_h) // 2 + 30

    options = ["Easy", "Meduim", "Hard", "Exterme"]
    rects = [
        pygame.Rect(start_x,               start_y,               card_w, card_h),
        pygame.Rect(start_x + card_w+gap_x,start_y,               card_w, card_h),
        pygame.Rect(start_x,               start_y + card_h+gap_y,card_w, card_h),
        pygame.Rect(start_x + card_w+gap_x,start_y + card_h+gap_y,card_w, card_h),
    ]

    # Backdrop
    vignette = pygame.Surface((WIN_WIDTH, WIN_HEIGHT), pygame.SRCALPHA)
    vignette.fill((0, 0, 0, 130))

    # Title button (fake button look for consistency)
    title_text = "Select Difficulty"
    subtitle_text = "Choose how tough you want it before the match begins."

    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                for name, r in zip(options, rects):
                    if r.collidepoint(mx, my):
                        return name

        # Draw
        WIN.blit(FULL_BG, (0, 0))
        WIN.blit(vignette, (0, 0))

        # Title
        render_outlined_text(WIN, title_text, FONT_72, (WIN_WIDTH // 2, 160),
                             SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL)
        render_outlined_text(WIN, subtitle_text, FONT_32, (WIN_WIDTH // 2, 210),
                             (240, 240, 240), SCORE_OUTLINE, SCORE_FILL)

        # Cards
        mx, my = pygame.mouse.get_pos()
        for name, r in zip(options, rects):
            hovered = r.collidepoint(mx, my)
            _card(WIN, r, name, DIFF_DESCRIPTIONS[name], hovered)

        # Hint
        hint = "Click a card • ESC to quit"
        hint_surf = FONT_24.render(hint, True, (220, 220, 220))
        WIN.blit(hint_surf, (WIN_WIDTH // 2 - hint_surf.get_width() // 2, WIN_HEIGHT - 60))

        pygame.display.update()

# -------------------------
# Main draw
# -------------------------

def draw_split_screen(surface, ai_birds, ai_pipes, human_bird, human_pipes,
                      ai_score, human_score, ai_lives, human_lives, level,
                      ai_game_over, human_game_over, ai_death_pause=0, human_death_pause=0):
    """Draw the split screen with AI on top and human on bottom (fast path)."""
    surface.fill((0, 0, 0))

    # --- AI area (upper) ---
    surface.blit(AI_BG, (0, 0))
    ai_area = pygame.Rect(0, 0, WIN_WIDTH, UPPER_HEIGHT)
    surface.set_clip(ai_area)

    for pipe in ai_pipes:
        ensure_pipe_scaled(pipe)
        scaled_top_height = int(pipe.height * HALF_RATIO)
        scaled_gap = int(pipe.GAP * HALF_RATIO)
        scaled_bottom_y = scaled_top_height + scaled_gap

        surface.blit(pipe.PIPE_TOP_UPPER, (pipe.x, scaled_top_height - pipe.PIPE_TOP_UPPER.get_height()))
        surface.blit(pipe.PIPE_BOTTOM_UPPER, (pipe.x, scaled_bottom_y))

    for bird in ai_birds:
        scaled_bird_y = int(bird.y * HALF_RATIO)
        temp_bird = Bird(bird.x, scaled_bird_y, "ai")
        temp_bird.tilt = bird.tilt
        temp_bird.jump_frame = bird.jump_frame
        temp_bird.draw(surface)
        bird.jump_frame = temp_bird.jump_frame

    surface.set_clip(None)
    draw_divider_line(surface)

    # --- Human area (lower) ---
    surface.blit(HUMAN_BG, (0, UPPER_HEIGHT))
    human_area = pygame.Rect(0, UPPER_HEIGHT, WIN_WIDTH, LOWER_HEIGHT)
    surface.set_clip(human_area)

    for pipe in human_pipes:
        ensure_pipe_scaled(pipe)
        scaled_top_height = int(pipe.height * HALF_RATIO)
        scaled_gap = int(pipe.GAP * HALF_RATIO)
        scaled_bottom_y = scaled_top_height + scaled_gap

        surface.blit(pipe.PIPE_TOP_LOWER, (pipe.x, UPPER_HEIGHT + scaled_top_height - pipe.PIPE_TOP_LOWER.get_height()))
        surface.blit(pipe.PIPE_BOTTOM_LOWER, (pipe.x, UPPER_HEIGHT + scaled_bottom_y))

    if human_bird:
        scaled_bird_y = int(human_bird.y * HALF_RATIO)
        temp_bird = Bird(human_bird.x, UPPER_HEIGHT + scaled_bird_y, "human")
        temp_bird.tilt = human_bird.tilt
        temp_bird.jump_frame = human_bird.jump_frame
        temp_bird.draw(surface)
        human_bird.jump_frame = temp_bird.jump_frame

    surface.set_clip(None)

    # UI labels
    render_outlined_text(surface, "MACHINE", FONT_32, (100, 20), SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL)
    render_outlined_text(surface, f"Score: {ai_score}", FONT_32, (100, 50), SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL)
    render_outlined_text(surface, f"Lives: {ai_lives}", FONT_32, (100, 80), SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL)
    render_outlined_text(surface, f"Birds: {len(ai_birds)}", FONT_32, (100, 110), SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL)

    render_outlined_text(surface, f"Level: {level}", FONT_32, (WIN_WIDTH - 100, 20), SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL)

    render_outlined_text(surface, "HUMAN", FONT_32, (100, UPPER_HEIGHT + 20), SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL)
    render_outlined_text(surface, f"Score: {human_score}", FONT_32, (100, UPPER_HEIGHT + 50), SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL)
    render_outlined_text(surface, f"Lives: {human_lives}", FONT_32, (100, UPPER_HEIGHT + 80), SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL)

    if ai_game_over:
        surface.blit(OVERLAY_AI_DEAD, (0, 0))
        render_outlined_text(surface, "MACHINE ELIMINATED", FONT_32,
                             (WIN_WIDTH // 2, UPPER_HEIGHT // 2),
                             (255, 255, 255), (255, 0, 0), (0, 0, 0))

    if human_game_over:
        surface.blit(OVERLAY_HUMAN_DEAD, (0, UPPER_HEIGHT))
        render_outlined_text(surface, "HUMAN ELIMINATED", FONT_32,
                             (WIN_WIDTH // 2, UPPER_HEIGHT + LOWER_HEIGHT // 2),
                             (255, 255, 255), (255, 0, 0), (0, 0, 0))

    if ai_death_pause > 0:
        render_outlined_text(surface, "MACHINE LOST A LIFE!", FONT_48,
                             (WIN_WIDTH // 2, UPPER_HEIGHT // 2 - 50),
                             SCORE_ORANGE, (0, 0, 0), (255, 255, 255))
        render_outlined_text(surface, f"Lives Remaining: {ai_lives}", FONT_48,
                             (WIN_WIDTH // 2, UPPER_HEIGHT // 2),
                             SCORE_ORANGE, (0, 0, 0), (255, 255, 255))
        if ai_lives > 0:
            render_outlined_text(surface, "Respawning...", FONT_48,
                                 (WIN_WIDTH // 2, UPPER_HEIGHT // 2 + 50),
                                 (255, 255, 100), (0, 0, 0), (255, 255, 255))

    if human_death_pause > 0:
        render_outlined_text(surface, "HUMAN LOST A LIFE!", FONT_48,
                             (WIN_WIDTH // 2, UPPER_HEIGHT + LOWER_HEIGHT // 2 - 50),
                             SCORE_ORANGE, (0, 0, 0), (255, 255, 255))
        render_outlined_text(surface, f"Lives Remaining: {human_lives}", FONT_48,
                             (WIN_WIDTH // 2, UPPER_HEIGHT + LOWER_HEIGHT // 2),
                             SCORE_ORANGE, (0, 0, 0), (255, 255, 255))
        if human_lives > 0:
            render_outlined_text(surface, "Respawning...", FONT_48,
                                 (WIN_WIDTH // 2, UPPER_HEIGHT + LOWER_HEIGHT // 2 + 50),
                                 (255, 255, 100), (0, 0, 0), (255, 255, 255))

    if ai_death_pause == 0 and human_death_pause == 0:
        render_outlined_text(surface,
                             "SPACE: Jump | ESC: Pause | R: Restart | M: Menu",
                             FONT_24, (WIN_WIDTH // 2, WIN_HEIGHT - 20),
                             SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL)

    pygame.display.update()

# -------------------------
# Game loop
# -------------------------

def main():
    """Main game loop for Man VS Machine mode (single trained AI bird only)."""
    global WIN
    WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    pygame.display.set_caption("Flappy Bird - Man VS Machine")

    # --- Difficulty select & paths ---
    chosen = select_difficulty_screen()  # "Easy"/"Meduim"/"Hard"/"Exterme"
    local_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(local_dir)  # Go up one level from scripts/ to project root
    config_path = os.path.join(project_root, "configs", DIFFICULTY_TO_CONFIG[chosen])
    winner_path = os.path.join(project_root, "data", DIFF_TO_WINNER[chosen])

    # Strict requirement: winner must exist
    if not os.path.exists(winner_path):
        raise FileNotFoundError(
            f"Trained genome not found for '{chosen}'. Expected file: {os.path.basename(winner_path)}"
        )

    # Load NEAT config + trained genome
    config = neat.config.Config(
        neat.DefaultGenome, neat.DefaultReproduction,
        neat.DefaultSpeciesSet, neat.DefaultStagnation,
        config_path
    )
    with open(winner_path, "rb") as f:
        trained_genome = pickle.load(f)

    # Build the single trained network and bird
    ai_nets = [neat.nn.FeedForwardNetwork.create(trained_genome, config)]
    ai_birds = [Bird(280, 250, "ai")]

    # Human player
    human_bird = Bird(280, 250, "human")

    # Game state
    ai_pipes = [Pipe(WIN_WIDTH + 20)]
    human_pipes = [Pipe(WIN_WIDTH + 20)]

    ai_score = 0
    human_score = 0
    ai_lives = MAX_LIVES
    human_lives = MAX_LIVES
    level = 1

    # Level progression (by pipes passed)
    ai_pipe_passed_count = 0
    human_pipe_passed_count = 0
    ai_current_gap = Pipe.BASIC_GAP
    human_current_gap = Pipe.BASIC_GAP

    ai_game_over = False
    human_game_over = False
    game_completely_over = False

    ai_passed_pipes = set()
    human_passed_pipes = set()

    ai_death_pause = 0
    human_death_pause = 0
    ai_death_cooldown = 0
    human_death_cooldown = 0

    paused = False
    return_to_menu = False

    run = True
    while run:
        clock.tick(FPS)

        # Pause state
        if paused:
            resume_button, restart_button, menu_button = draw_pause_menu(WIN)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    paused = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if resume_button.is_clicked(pygame.mouse.get_pos(), True):
                        paused = False
                    if restart_button.is_clicked(pygame.mouse.get_pos(), True):
                        return main()
                    if menu_button.is_clicked(pygame.mouse.get_pos(), True):
                        return_to_menu = True
                        run = False
            continue

        # Game completely over
        if game_completely_over:
            draw_game_over_screen(WIN, ai_score, human_score, ai_lives, human_lives)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        return main()
                    elif event.key == pygame.K_m:
                        return_to_menu = True
                        run = False
            continue

        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not human_game_over:
                    human_bird.jump()
                elif event.key == pygame.K_ESCAPE:
                    paused = True
                elif event.key == pygame.K_r:
                    return main()
                elif event.key == pygame.K_m:
                    return_to_menu = True
                    run = False

        # -----------------
        # AI logic (single trained bird)
        # -----------------
        if not ai_game_over and len(ai_birds) > 0 and ai_death_pause == 0:
            # relevant pipe index
            pipe_ind = 0
            if len(ai_pipes) > 1 and ai_birds[0].x > ai_pipes[0].x + ai_pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1

            # Move + NN decision
            bird = ai_birds[0]
            bird.move()
            output = ai_nets[0].activate((
                bird.y,
                abs(bird.y - ai_pipes[pipe_ind].height),
                abs(bird.y - ai_pipes[pipe_ind].bottom)
            ))
            if output[0] > 0.5:
                bird.jump()

        # -----------------
        # Human logic
        # -----------------
        if not human_game_over and human_bird and human_death_pause == 0:
            human_bird.move()

        # -----------------
        # AI pipes & collisions
        # -----------------
        if not ai_game_over and ai_death_pause == 0:
            rem_ai = []
            add_ai_pipe = False

            for pipe in ai_pipes:
                pipe.move()

                # Collision
                if ai_birds and pipe.collide(ai_birds[0]):
                    # trained bird "dies"
                    del ai_nets[0]
                    del ai_birds[0]

                # Pass tracking
                if ai_birds and pipe not in ai_passed_pipes and pipe.x < ai_birds[0].x:
                    ai_passed_pipes.add(pipe)
                    add_ai_pipe = True

                # Off-screen
                if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                    rem_ai.append(pipe)
                    ai_passed_pipes.discard(pipe)

            if add_ai_pipe:
                ai_score += 1
                ai_pipe_passed_count += 1

                # Level progression (AI)
                if ai_pipe_passed_count % 15 == 0:
                    ai_current_gap = max(Pipe.MIN_GAP, ai_current_gap - Pipe.CHANGE_IN_GAP)
                    if ai_current_gap != Pipe.MIN_GAP:
                        level += 1

            # spawn new pipe
            if ai_pipes and ai_pipes[-1].x < 700:
                ai_pipes.append(Pipe(WIN_WIDTH + 20, gap=ai_current_gap))

            # remove off-screen
            for r in rem_ai:
                ai_pipes.remove(r)

            # Bounds kill
            if ai_birds:
                b = ai_birds[0]
                if b.y + b.img.get_height() - 10 >= WIN_HEIGHT or b.y < -50:
                    del ai_nets[0]
                    del ai_birds[0]

        # -----------------
        # Human pipes & collisions
        # -----------------
        if not human_game_over and human_bird and human_death_pause == 0:
            rem_human = []
            add_human_pipe = False

            for pipe in human_pipes:
                pipe.move()

                # Collision
                if human_bird and pipe.collide(human_bird) and human_death_cooldown == 0:
                    human_lives -= 1
                    human_death_pause = 120
                    human_death_cooldown = 180
                    if human_lives <= 0:
                        human_game_over = True
                        human_bird = None

                # Pass tracking
                if human_bird and pipe not in human_passed_pipes and pipe.x < human_bird.x:
                    human_passed_pipes.add(pipe)
                    add_human_pipe = True

                # Off-screen
                if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                    rem_human.append(pipe)
                    human_passed_pipes.discard(pipe)

            if add_human_pipe:
                human_score += 1
                human_pipe_passed_count += 1

                # Level progression (human)
                if human_pipe_passed_count % 15 == 0:
                    human_current_gap = max(Pipe.MIN_GAP, human_current_gap - Pipe.CHANGE_IN_GAP)

            # spawn new pipe
            if human_pipes and human_pipes[-1].x < 700:
                human_pipes.append(Pipe(WIN_WIDTH + 20, gap=human_current_gap))

            # remove off-screen
            for r in rem_human:
                human_pipes.remove(r)

            # Bounds kill
            if (human_bird and human_death_cooldown == 0 and
                (human_bird.y + human_bird.img.get_height() - 10 >= WIN_HEIGHT or human_bird.y < -50)):
                human_lives -= 1
                human_death_pause = 120
                human_death_cooldown = 180
                if human_lives <= 0:
                    human_game_over = True
                    human_bird = None

        # -----------------
        # AI life loss gate
        # -----------------
        if not ai_game_over and len(ai_birds) == 0 and ai_death_cooldown == 0 and ai_death_pause == 0:
            ai_lives -= 1
            ai_death_pause = 120
            ai_death_cooldown = 180
            if ai_lives <= 0:
                ai_game_over = True

        # Game completely over?
        if ai_game_over and human_game_over:
            game_completely_over = True

        # Death pause / respawn
        if ai_death_pause > 0:
            ai_death_pause -= 1
            if ai_death_pause == 0 and ai_lives > 0 and not ai_game_over:
                # Respawn SAME trained bird
                ai_nets.clear()
                ai_birds.clear()
                ai_pipes = [Pipe(WIN_WIDTH + 20)]
                ai_nets.append(neat.nn.FeedForwardNetwork.create(trained_genome, config))
                ai_birds.append(Bird(280, 250, "ai"))

        if human_death_pause > 0:
            human_death_pause -= 1
            if human_death_pause == 0 and human_lives > 0 and not human_game_over:
                human_pipes = [Pipe(WIN_WIDTH + 20)]
                human_bird = Bird(280, 250, "human")

        # Cooldowns ticking
        if ai_death_cooldown > 0:
            ai_death_cooldown -= 1
        if human_death_cooldown > 0:
            human_death_cooldown -= 1

        # Draw frame
        draw_split_screen(
            WIN, ai_birds, ai_pipes, human_bird, human_pipes,
            ai_score, human_score, ai_lives, human_lives, level,
            ai_game_over, human_game_over, ai_death_pause, human_death_pause
        )

    # Return to menu?
    if return_to_menu:
        from src.ui import menu
        menu.run_menu()

    pygame.quit()


if __name__ == "__main__":
    main()
