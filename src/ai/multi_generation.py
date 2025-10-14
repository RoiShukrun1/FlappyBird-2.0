import pygame
import neat
import os
import random
import sys

from ..core.bird import Bird
from ..core.pipe import Pipe
from ..core.assets import BG_IMG, SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL
from ..ui.button import Button, render_outlined_text

# Game settings
WIN_WIDTH = 800
WIN_HEIGHT = 800
FLOOR = 730  # Still used for collision with the floor

WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Flappy Bird NEAT - Level System")

clock = pygame.time.Clock()

# Pause menu settings
PAUSE_OVERLAY_COLOR = (0, 0, 0, 180)  # Semi-transparent black
PAUSE_BUTTON_WIDTH = 200
PAUSE_BUTTON_HEIGHT = 60
PAUSE_BUTTON_MARGIN = 20

# Level up animation settings
LEVEL_UP_DURATION = 120  # frames (2 seconds at 60 FPS)
LEVEL_UP_COLOR = SCORE_ORANGE  # Use orange color for level up text

# Game modes
MODE_LEVELS = "levels"
MODE_MOVING = "moving"

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
        "Resume"
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
    
    # Update and draw buttons
    resume_button.check_hover(mouse_pos)
    resume_button.draw(surface)
    
    menu_button.check_hover(mouse_pos)
    menu_button.draw(surface)
    
    pygame.display.update()
    
    return resume_button, menu_button

def draw_level_up_animation(surface, frame):
    """Draw the animated LEVEL UP! text"""
    # Calculate animation parameters based on current frame
    alpha = 255
    scale = 1.0
    
    # First half of animation: text grows and stays fully opaque
    if frame < LEVEL_UP_DURATION / 2:
        scale = 0.5 + (frame / (LEVEL_UP_DURATION / 2)) * 0.5  # Scale from 0.5 to 1.0
    # Second half: text fades out
    else:
        alpha = 255 * (1 - (frame - LEVEL_UP_DURATION / 2) / (LEVEL_UP_DURATION / 2))
    
    # Create the level up text font
    base_size = 72
    font_size = int(base_size * scale)
    level_font = pygame.font.Font(None, font_size)
    
    # Create a transparent surface for the level up text
    text_surface = pygame.Surface((WIN_WIDTH, 200), pygame.SRCALPHA)
    
    # Calculate vertical movement (starts at bottom, moves to center)
    y_pos = WIN_HEIGHT // 2
    if frame < LEVEL_UP_DURATION / 3:
        y_offset = (1 - frame / (LEVEL_UP_DURATION / 3)) * 100
        y_pos += y_offset
    
    # Render the level up text with animation effects
    render_outlined_text(
        text_surface,
        "LEVEL UP!",
        level_font,
        (WIN_WIDTH // 2, 100),
        (*LEVEL_UP_COLOR, int(alpha)),
        (0, 0, 0, int(alpha * 0.8)),
        (255, 255, 255, int(alpha * 0.6))
    )
    
    # Apply the text surface to the main surface
    surface.blit(text_surface, (0, y_pos - 100))

# Draw game window (without base)
def draw_window(win, birds, pipes, score, gen, mode, level=1, level_up_frame=None):
    win.blit(BG_IMG, (0, 0))
    
    for pipe in pipes:
        pipe.draw(win)
    
    for bird in birds:
        bird.draw(win)
    
    # Create custom font similar to what's used in main.py
    font = pygame.font.Font(None, 40)
    
    # Display score with stylized text in top center
    render_outlined_text(
        win, 
        "Score: " + str(score), 
        font, 
        (WIN_WIDTH // 2, 30),
        SCORE_ORANGE,
        SCORE_OUTLINE,
        SCORE_FILL
    )
    
    # Display generation in top left with stylized text
    render_outlined_text(
        win, 
        "Gen: " + str(gen), 
        font, 
        (80, 30),
        SCORE_ORANGE,
        SCORE_OUTLINE,
        SCORE_FILL
    )
    
    # Display alive birds count with stylized text
    render_outlined_text(
        win, 
        "Alive: " + str(len(birds)), 
        font, 
        (80, 70),
        SCORE_ORANGE,
        SCORE_OUTLINE,
        SCORE_FILL
    )
    
    # Display mode-specific information
    if mode == MODE_LEVELS:
        # Display level with stylized text
        render_outlined_text(
            win, 
            "Level: " + str(level), 
            font, 
            (WIN_WIDTH - 80, 30),
            SCORE_ORANGE,
            SCORE_OUTLINE,
            SCORE_FILL
        )
        
        # Draw level up animation if active
        if level_up_frame is not None and level_up_frame < LEVEL_UP_DURATION:
            draw_level_up_animation(win, level_up_frame)
    else:  # Moving pipes mode
        # Display mode with stylized text
        render_outlined_text(
            win, 
            "Mode: Moving", 
            font, 
            (WIN_WIDTH - 100, 30),
            SCORE_ORANGE,
            SCORE_OUTLINE,
            SCORE_FILL
        )

        # Display mode with stylized text
        render_outlined_text(
            win, 
            "Pipes", 
            font, 
            (WIN_WIDTH - 60, 60),
            SCORE_ORANGE,
            SCORE_OUTLINE,
            SCORE_FILL
        )
    
    # Control hints (AI mode - no jump control needed)
    hint_font = pygame.font.Font(None, 24)
    render_outlined_text(
        win,
        "ESC: Pause | R: Restart | M: Menu",
        hint_font,
        (WIN_WIDTH // 2, WIN_HEIGHT - 20),
        SCORE_ORANGE,
        SCORE_OUTLINE,
        SCORE_FILL
    )
    
    pygame.display.update()

# Global generation counter
gen = 0

def eval_genomes(genomes, config, mode=MODE_LEVELS):
    global gen
    gen += 1
    
    # Set window caption based on mode
    if mode == MODE_LEVELS:
        pygame.display.set_caption("Flappy Bird NEAT - Level System")
    else:  # mode == MODE_MOVING
        pygame.display.set_caption("Flappy Bird NEAT - Moving Pipes")

    nets = []
    birds = []
    ge = []
    
    # Create neural networks and bird instances for each genome
    for genome_id, genome in genomes:
        genome.fitness = 0  # Start fitness at 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        ge.append(genome)
    
    # Initialize pipes based on mode
    if mode == MODE_LEVELS:
        pipes = [Pipe(WIN_WIDTH + 100)]
        pipe_passed_count = 0
        current_gap = Pipe.BASIC_GAP
        level = 1
        level_up_frame = None
    else:  # mode == MODE_MOVING
        pipes = [Pipe(WIN_WIDTH + 100, moving=True)]
    
    score = 0
    paused = False
    return_to_menu = False
    
    run = True
    while run and len(birds) > 0:
        clock.tick(60)
        
        # Handle pause state
        if paused:
            resume_button, menu_button = draw_pause_menu(WIN)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    paused = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Check if resume button is clicked
                    if resume_button.is_clicked(pygame.mouse.get_pos(), True):
                        paused = False
                    # Check if menu button is clicked
                    if menu_button.is_clicked(pygame.mouse.get_pos(), True):
                        # Set flag to return to menu instead of calling directly
                        return_to_menu = True
                        run = False
            
            continue  # Skip the rest of the game logic while paused
        
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = True
                elif event.key == pygame.K_m:
                    # Set flag to return to menu instead of calling directly
                    return_to_menu = True
                    run = False
        
        # Only determine pipe_ind if birds exist
        if len(birds) > 0:
            pipe_ind = 0
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1

        # Move birds and update fitness
        for i, bird in enumerate(birds):
            bird.move()
            ge[i].fitness += 1
            
            output = nets[i].activate((bird.y,abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))
            if output[0] > 0.5:
                bird.jump()
        
        rem = []
        add_pipe = False

        for pipe in pipes:
            # Moving pipes logic (only for moving pipes mode)
            if mode == MODE_MOVING and pipe.moving:
                if pipe.motionToTop:
                    pipe.moveUp()
                else:
                    pipe.moveDown()

            pipe.move()
            
            # Check for collision with any bird
            for i, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[i].fitness -= 1
                    nets.pop(i)
                    ge.pop(i)
                    birds.pop(i)
            
            # Mark pipe for removal if it goes off-screen
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)
            
            # Only check if there are birds remaining before accessing birds[0]
            if birds and (not pipe.passed and pipe.x < birds[0].x):
                pipe.passed = True
                add_pipe = True
        
        if add_pipe:
            score += 1
            for genome in ge:
                genome.fitness += 5

            # Mode-specific pipe creation logic
            if mode == MODE_LEVELS:
                pipe_passed_count += 1
                # Level progression logic - Now every 15 pipes decrease the gap
                if pipe_passed_count % 15 == 0:
                    current_gap = max(Pipe.MIN_GAP, current_gap - Pipe.CHANGE_IN_GAP)
                    if current_gap != Pipe.MIN_GAP:
                        level += 1
                        # Give bonus fitness when reaching a new level
                        for genome in ge:
                            genome.fitness += 15
                        
                        # Start level up animation
                        level_up_frame = 0
                
                pipes.append(Pipe(WIN_WIDTH + 100, gap=current_gap))
            else:  # mode == MODE_MOVING
                # All pipes are moving in this mode
                pipes.append(Pipe(WIN_WIDTH + 100, moving=True))

        # Remove off-screen pipes
        for r in rem:
            pipes.remove(r)
        
        # Check if birds hit the floor or fly too high
        for i, bird in enumerate(birds):
            if bird.y + bird.img.get_height() - 10 >= FLOOR or bird.y < -50:
                nets.pop(i)
                ge.pop(i)
                birds.pop(i)
        
        # Update level up animation frame if active (levels mode only)
        if mode == MODE_LEVELS and level_up_frame is not None:
            if level_up_frame < LEVEL_UP_DURATION:
                level_up_frame += 1
            else:
                level_up_frame = None
        
        # Draw window with current game state
        if mode == MODE_LEVELS:
            draw_window(WIN, birds, pipes, score, gen, mode, level, level_up_frame)
        else:  # mode == MODE_MOVING
            draw_window(WIN, birds, pipes, score, gen, mode)
    
    # After exiting the main game loop, check if we need to return to menu
    if return_to_menu:
        return "menu"
    
    return None

def run(config_file, mode=MODE_LEVELS):
    """
    Run the NEAT algorithm to train a neural network to play Flappy Bird.
    
    Args:
        config_file: Path to the config file for NEAT
        mode: Game mode - either "levels" for decreasing gaps or "moving" for moving pipes
    """
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_file)
    
    p = neat.Population(config)
    
    # Optional: Add reporters to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    
    # Modify the fitness function to handle menu navigation
    def fitness_with_menu(genomes, config):
        result = eval_genomes(genomes, config, mode)
        if result == "menu":
            # Return to menu
            from ..ui import menu
            menu.run_menu()
            return
        
    # Run NEAT algorithm for up to 50 generations with the specified mode.
    try:
        winner = p.run(fitness_with_menu, 50)
        print('\nBest genome:\n{!s}'.format(winner))
    except Exception as e:
        print(f"Exception during training: {e}")
        # If error occurs, just return to menu
        import menu
        menu.run_menu()

def run_levels(config_file):
    """Run NEAT with level system (decreasing gaps)"""
    run(config_file, MODE_LEVELS)

def run_moving(config_file):
    """Run NEAT with moving pipes"""
    run(config_file, MODE_MOVING)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "..", "..", "configs", "config-feedforward.txt")
    
    # Default to level mode if no arguments provided
    mode = MODE_LEVELS
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "moving":
            mode = MODE_MOVING
    
    run(config_path, mode)
