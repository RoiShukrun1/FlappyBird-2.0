import pygame
import os

pygame.init()

# Colors for score display
SCORE_ORANGE = (255, 140, 100)  # Coral/orange color
SCORE_OUTLINE = (20, 20, 60)    # Dark blue/navy
SCORE_FILL = (255, 255, 255)    # White fill

# Background remains unchanged
BG_IMG = pygame.transform.rotozoom(pygame.image.load(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "bg.png")), 0, 1)

# Scale the pipe image to 50% of its original size
original_pipe = pygame.image.load(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "pipe.png"))
PIPE_IMG = pygame.transform.rotozoom(original_pipe, 0, 0.5)

# Scale the bird image to smaller size
BIRD_IMGS = [
    pygame.transform.rotozoom(pygame.image.load(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "bird1.png")), 0, 0.1),
    pygame.transform.rotozoom(pygame.image.load(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "bird2.png")), 0, 0.1)
]

# AI bird images - scaled smaller to match original bird size
BIRD_AI_IMGS = [
    pygame.transform.rotozoom(pygame.image.load(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "bird-ai1.png")), 0, 0.05),
    pygame.transform.rotozoom(pygame.image.load(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "bird-ai2.png")), 0, 0.05)
]

# Human bird images - scaled smaller to match original bird size
BIRD_HUMAN_IMGS = [
    pygame.transform.rotozoom(pygame.image.load(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "bird-human1.png")), 0, 0.05),
    pygame.transform.rotozoom(pygame.image.load(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "bird-human2.png")), 0, 0.05)
]

# Load and scale the game over image to 50% of its original size
gameover_original = pygame.image.load(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "gameover.png"))
GAMEOVER_IMG = pygame.transform.rotozoom(gameover_original, 0, 0.5)

# Font for score display
SCORE_FONT = pygame.font.Font(None, 50)
FINAL_SCORE_FONT = pygame.font.Font(None, 70)
