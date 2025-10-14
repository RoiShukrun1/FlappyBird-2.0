import pygame
import random
from .assets import PIPE_IMG

class Pipe: 
    BASIC_GAP = 300
    CHANGE_IN_GAP = 30
    MIN_GAP = 200
    VEL = 5
    MIN_HEIGHT = 100
    MAX_HEIGHT = 500

    def __init__(self, x, gap=None, moving=False):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG
        self.passed = False
        self.motionToTop = random.randint(0, 1)
        self.moving = moving
        self.GAP = gap if gap else Pipe.BASIC_GAP
        self.set_height()

    def set_height(self):
        self.height = random.randrange(self.MIN_HEIGHT, self.MAX_HEIGHT)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def moveUp(self):
        amount = 3
        if self.height - amount >= self.MIN_HEIGHT:
            self.height -= amount
            self.top = self.height - self.PIPE_TOP.get_height()
            self.bottom = self.height + self.GAP
        else:
            self.motionToTop = not self.motionToTop

    def moveDown(self):
        amount = 3
        if self.height + amount <= self.MAX_HEIGHT:
            self.height += amount
            self.top = self.height - self.PIPE_TOP.get_height()
            self.bottom = self.height + self.GAP
        else:
            self.motionToTop = not self.motionToTop

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        return t_point or b_point
