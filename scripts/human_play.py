import pygame
from src.core.assets import (BG_IMG, GAMEOVER_IMG, SCORE_FONT, FINAL_SCORE_FONT,
                   SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL)
from src.core.pipe import Pipe
from src.core.bird import Bird
from src.utils.best_score import load_best_score, save_best_score
from src.ui.button import Button, render_outlined_text

pygame.init()

WIN_WIDTH = 800
WIN_HEIGHT = 800
win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
clock = pygame.time.Clock()

# Pause menu settings
PAUSE_OVERLAY_COLOR = (0, 0, 0, 180)  # Semi-transparent black
PAUSE_BUTTON_WIDTH = 200
PAUSE_BUTTON_HEIGHT = 60
PAUSE_BUTTON_MARGIN = 20

def draw_pause_menu(surface):
    # Use background image instead of semi-transparent overlay
    surface.blit(BG_IMG, (0, 0))
    
    # Create a semi-transparent overlay on top of the background
    overlay = pygame.Surface((WIN_WIDTH, WIN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 120))  # Less opaque black
    surface.blit(overlay, (0, 0))
    
    # Create pause title text
    title_font = pygame.font.Font(None, 72)
    render_outlined_text(
        surface,
        "PAUSED",
        title_font,
        (WIN_WIDTH // 2, WIN_HEIGHT // 3),
        SCORE_ORANGE,
        SCORE_OUTLINE,
        SCORE_FILL
    )
    
    # Create buttons
    resume_button = Button(
        (WIN_WIDTH - PAUSE_BUTTON_WIDTH) // 2,
        WIN_HEIGHT // 2,
        PAUSE_BUTTON_WIDTH,
        PAUSE_BUTTON_HEIGHT,
        "Resume Game"
    )
    
    menu_button = Button(
        (WIN_WIDTH - PAUSE_BUTTON_WIDTH) // 2,
        WIN_HEIGHT // 2 + PAUSE_BUTTON_HEIGHT + PAUSE_BUTTON_MARGIN,
        PAUSE_BUTTON_WIDTH,
        PAUSE_BUTTON_HEIGHT,
        "Main Menu"
    )
    
    # Get mouse position and check for clicks
    mouse_pos = pygame.mouse.get_pos()
    mouse_clicked = pygame.mouse.get_pressed()[0]
    
    # Update and draw buttons
    resume_button.check_hover(mouse_pos)
    resume_button.draw(surface)
    
    menu_button.check_hover(mouse_pos)
    menu_button.draw(surface)
    
    pygame.display.update()
    
    return resume_button, menu_button

def draw_window(win, bird, pipes, score, game_over=False, best_score=0):
    win.blit(BG_IMG, (0, 0))
    for pipe in pipes:
        pipe.draw(win)
    bird.draw(win)
    
    # Draw current score with game over style
    render_outlined_text(
        win, 
        str(score), 
        SCORE_FONT, 
        (WIN_WIDTH // 2, 50),
        SCORE_ORANGE,
        SCORE_OUTLINE,
        SCORE_FILL
    )
    
    if game_over:
        # Center the game over image
        game_over_x = (WIN_WIDTH - GAMEOVER_IMG.get_width()) // 2
        game_over_y = (WIN_HEIGHT - GAMEOVER_IMG.get_height()) // 2
        win.blit(GAMEOVER_IMG, (game_over_x, game_over_y))
        
        # Draw final score with game over style
        render_outlined_text(
            win,
            f"Final Score: {score}",
            FINAL_SCORE_FONT,
            (WIN_WIDTH // 2, game_over_y + GAMEOVER_IMG.get_height() + 50),
            SCORE_ORANGE,
            SCORE_OUTLINE,
            SCORE_FILL
        )
        
        # Draw best score under final score
        render_outlined_text(
            win,
            f"Best Score: {best_score}",
            FINAL_SCORE_FONT,
            (WIN_WIDTH // 2, game_over_y + GAMEOVER_IMG.get_height() + 120),
            SCORE_ORANGE,
            SCORE_OUTLINE,
            SCORE_FILL
        )
    
    # Control hints (only when not game over)
    if not game_over:
        hint_font = pygame.font.Font(None, 24)
        render_outlined_text(
            win,
            "SPACE: Jump | ESC: Pause | R: Restart | M: Menu",
            hint_font,
            (WIN_WIDTH // 2, WIN_HEIGHT - 20),
            SCORE_ORANGE,
            SCORE_OUTLINE,
            SCORE_FILL
        )
    
    pygame.display.update()

def main(best_score_override=None):
    """
    Runs single-player and returns the final score to the caller.
    If best_score_override is provided (e.g., server best for logged-in user),
    it is displayed instead of the local best.
    """
    bird = Bird(300, 500)
    pipes = [Pipe(800)]
    run = True
    game_over = False
    paused = False
    score = 0
    best_score = best_score_override if best_score_override is not None else load_best_score()
    passed_pipes = set()  # Keep track of passed pipes to avoid double counting
    
    while run:
        clock.tick(60) 

        # Handle pause state
        if paused:
            resume_button, menu_button = draw_pause_menu(win)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return score
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    paused = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Check if resume button is clicked
                    if resume_button.is_clicked(pygame.mouse.get_pos(), True):
                        paused = False
                    # Check if menu button is clicked
                    if menu_button.is_clicked(pygame.mouse.get_pos(), True):
                        # Save best score before returning to menu
                        best_score = save_best_score(score)
                        return score
            
            continue  # Skip the rest of the game logic while paused
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird.jump()
                elif event.key == pygame.K_ESCAPE and not game_over:
                    paused = True
                elif event.key == pygame.K_r and game_over:
                    # Save best score before resetting
                    best_score = save_best_score(score)
                    # Reset game when R is pressed after game over
                    bird = Bird(300, 500)
                    pipes = [Pipe(800)]
                    game_over = False
                    score = 0
                    passed_pipes.clear()
                elif event.key == pygame.K_m:
                    # M key always returns to menu
                    best_score = save_best_score(score)
                    return score

        if not game_over:
            bird.move()
            remove = []
            for pipe in pipes:
                pipe.move()
                # Check collision between the bird and the pipe
                if pipe.collide(bird):
                    game_over = True
                    # Update best score when game ends
                    best_score = save_best_score(score)
                if bird.y > WIN_HEIGHT or bird.y < 0:
                    game_over = True
                    # Update best score when game ends
                    best_score = save_best_score(score)
                # Score point when passing a pipe
                if pipe.x + pipe.PIPE_TOP.get_width() < bird.x and pipe not in passed_pipes:
                    score += 1
                    passed_pipes.add(pipe)
                # Remove off-screen pipes
                if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                    remove.append(pipe)

            # Remove off-screen pipes
            for r in remove:
                pipes.remove(r)
            # Add a new pipe when needed
            if pipes and pipes[-1].x < 450:
                pipes.append(Pipe(WIN_WIDTH))

        draw_window(win, bird, pipes, score, game_over, best_score)

    pygame.quit()
    return score

if __name__ == "__main__":
    main()