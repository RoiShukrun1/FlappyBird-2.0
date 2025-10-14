import pygame
from .assets import BIRD_IMGS, BIRD_AI_IMGS, BIRD_HUMAN_IMGS

class Bird:
    GRAVITY = 0.3
    JUMP_VEL = -6.5
    MAX_ROTATION = 15
    ROT_VEL = 10
    def __init__(self, x, y, bird_type="default"):
        self.x = x
        self.y = y
        self.vel = 0
        self.tick_count = 0
        self.height = self.y
        self.tilt = 0
        self.img_count = 0
        self.bird_type = bird_type
        
        # Choose the appropriate image set based on bird type
        if bird_type == "ai":
            self.bird_imgs = BIRD_AI_IMGS
        elif bird_type == "human":
            self.bird_imgs = BIRD_HUMAN_IMGS
        else:
            self.bird_imgs = BIRD_IMGS  # Default images
            
        self.img = self.bird_imgs[0]
        self.jump_frame = 0

    def jump(self):
        self.vel = self.JUMP_VEL
        self.height = self.y
        self.jump_frame = 10

    def move(self):
        # Increase velocity by gravity (accelerating fall)
        self.vel += self.GRAVITY

        #Update position based on velocity
        self.y += self.vel

        #Update tilt relative to falling velocity:
        if self.vel < 0:
            self.tilt = self.MAX_ROTATION
        else:
            new_tilt = self.MAX_ROTATION - self.vel * 7.5
            # Clamp the downward tilt to -38 degrees maximum
            if new_tilt < -38:
                new_tilt = -38
            self.tilt = new_tilt

    def draw(self, win):
        # Choose bird2 for one frame when jump_frame is active
        if self.jump_frame > 0:
            current_img = self.bird_imgs[1]
            self.jump_frame -= 1  # After drawing once, reset to bird1
        else:
            current_img = self.bird_imgs[0]

        rotated_image = pygame.transform.rotate(current_img, self.tilt)
        new_rect = rotated_image.get_rect(center=current_img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        # Use the current image for collision detection
        if self.jump_frame > 0:
            current_img = self.bird_imgs[1]
        else:
            current_img = self.bird_imgs[0]
        return pygame.mask.from_surface(current_img)
