import pygame
import math
from ..core.assets import SCORE_ORANGE, SCORE_OUTLINE, SCORE_FILL

# Button properties with improved color scheme
BUTTON_COLOR = (52, 152, 219)  # Modern blue
BUTTON_HOVER_COLOR = (41, 128, 185)  # Darker blue
BUTTON_ACTIVE_COLOR = (46, 204, 113)  # Green for active state
BUTTON_SHADOW_COLOR = (44, 62, 80)  # Dark shadow
TEXT_COLOR = (255, 255, 255)  # White
BUTTON_BORDER_COLOR = (236, 240, 241)  # Light border

# Function to draw gradient rectangle
def draw_gradient_rect(surface, rect, color1, color2, vertical=True):
    """Draw a gradient rectangle"""
    if vertical:
        for y in range(rect.height):
            ratio = y / rect.height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            pygame.draw.line(surface, (r, g, b), (rect.x, rect.y + y), (rect.x + rect.width, rect.y + y))
    else:
        for x in range(rect.width):
            ratio = x / rect.width
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            pygame.draw.line(surface, (r, g, b), (rect.x + x, rect.y), (rect.x + x, rect.y + rect.height))

# Function to draw shadow
def draw_shadow(surface, rect, shadow_color, offset=3, blur=2):
    """Draw a shadow for the rectangle"""
    shadow_rect = pygame.Rect(rect.x + offset, rect.y + offset, rect.width, rect.height)
    
    # Create shadow surface with alpha
    shadow_surface = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
    
    # Draw multiple shadow layers for blur effect
    for i in range(blur):
        alpha = 50 - i * 15
        if alpha > 0:
            shadow_surface.set_alpha(alpha)
            pygame.draw.rect(shadow_surface, shadow_color, (0, 0, shadow_rect.width, shadow_rect.height), border_radius=10)
            surface.blit(shadow_surface, shadow_rect)

# Function to render outlined text with special styling
def render_outlined_text(surface, text, font, pos, text_color, outline_color, fill_color):
    # Render the outline by offsetting the text in multiple directions
    outline_positions = [(-2, -2), (-2, 2), (2, -2), (2, 2), (-2, 0), (2, 0), (0, -2), (0, 2)]
    x, y = pos
    
    # First render the outline
    for dx, dy in outline_positions:
        outline_text = font.render(text, True, outline_color)
        outline_rect = outline_text.get_rect(center=(x + dx, y + dy))
        surface.blit(outline_text, outline_rect)
    
    # Then render the fill
    fill_text = font.render(text, True, fill_color)
    fill_rect = fill_text.get_rect(center=(x, y))
    surface.blit(fill_text, fill_rect)
    
    # Finally render the colored text
    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=(x, y))
    surface.blit(text_surface, text_rect)

class Button:
    def __init__(self, x, y, width, height, text, font_size=36):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, font_size)
        self.color = BUTTON_COLOR
        self.hover_color = BUTTON_HOVER_COLOR
        self.active_color = BUTTON_ACTIVE_COLOR
        self.is_hovered = False
        self.is_clicked_state = False
        self.animation_time = 0
        
    def draw(self, surface):
        # Draw shadow
        draw_shadow(surface, self.rect, BUTTON_SHADOW_COLOR, offset=4, blur=3)
        
        # Determine button color based on state
        if self.is_clicked_state:
            color = self.active_color
        elif self.is_hovered:
            color = self.hover_color
        else:
            color = self.color
        
        # Create gradient colors
        color_dark = tuple(max(0, c - 30) for c in color)
        color_light = tuple(min(255, c + 20) for c in color)
        
        # Draw gradient background
        draw_gradient_rect(surface, self.rect, color_light, color_dark, vertical=True)
        
        # Draw border with rounded corners
        pygame.draw.rect(surface, BUTTON_BORDER_COLOR, self.rect, 2, border_radius=12)
        
        # Add inner highlight
        inner_rect = pygame.Rect(self.rect.x + 2, self.rect.y + 2, self.rect.width - 4, self.rect.height - 4)
        highlight_color = tuple(min(255, c + 40) for c in color)
        pygame.draw.rect(surface, highlight_color, inner_rect, 1, border_radius=10)
        
        # Add subtle glow effect when hovered
        if self.is_hovered:
            glow_rect = pygame.Rect(self.rect.x - 2, self.rect.y - 2, self.rect.width + 4, self.rect.height + 4)
            glow_surface = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            glow_surface.set_alpha(30)
            pygame.draw.rect(glow_surface, color, (0, 0, glow_rect.width, glow_rect.height), border_radius=14)
            surface.blit(glow_surface, glow_rect)
        
        # Render button text with improved styling
        text_color = TEXT_COLOR
        if self.is_clicked_state:
            text_color = (255, 255, 255)  # Bright white for active state
        
        render_outlined_text(
            surface,
            self.text,
            self.font,
            self.rect.center,
            text_color,
            SCORE_OUTLINE,
            SCORE_FILL
        )
    
    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered
    
    def is_clicked(self, mouse_pos, mouse_click):
        clicked = self.rect.collidepoint(mouse_pos) and mouse_click
        if clicked:
            self.is_clicked_state = True
            # Reset clicked state after a short delay
            pygame.time.set_timer(pygame.USEREVENT + 1, 150)
        return clicked
    
    def update(self, dt):
        """Update button animations"""
        self.animation_time += dt 