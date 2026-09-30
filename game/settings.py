"""Sizes, speeds, and colours for the zebra window.

The game draws a small world and stretches it, which keeps the pixels chunky.
"""
import os

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 720
FPS = 60

WORLD_WIDTH = 800
WORLD_HEIGHT = 720

GROUND_Y = 600
GRAVITY = 0.65
JUMP_VELOCITY = -18.0
BOUNCE_VELOCITY = -10.0
SCROLL_SPEED = 3.5

# One forecast day equals this many pixels of track.
PIXELS_PER_DAY = 220

ZEBRA_X = 100
ZEBRA_W = 240
ZEBRA_H = 180

# Dynamic scaling based on amount
ROCK_MIN_SIZE = 50
ROCK_MAX_SIZE = 160
COIN_MIN_SIZE = 50
COIN_MAX_SIZE = 120

# Colors for Pastel Theme
COLOUR_SKY = (174, 217, 224)       # Pastel Blue
COLOUR_SKY_DANGER = (255, 182, 193) # Pastel Red/Pink
COLOUR_GROUND = (210, 180, 140)    # Pastel Light Brown (Tan)
COLOUR_GRASS = (152, 251, 152)     # Pastel Pale Green
COLOUR_LEAVES = (143, 188, 143)    # Pastel Dark Sea Green
COLOUR_ZEBRA_DARK = (50, 50, 50)
COLOUR_ZEBRA_LIGHT = (245, 245, 230)
COLOUR_ROCK = (168, 64, 64)        
COLOUR_COIN = (255, 179, 71)       # Pastel Orange
COLOUR_TEXT = (255, 255, 255)
COLOUR_TEXT_OUTLINE = (0, 0, 0)
COLOUR_HUD = (143, 188, 143, 180)  # Pastel translucent green
COLOUR_BTN_BG = (50, 205, 50)      # Bright Green for buttons

# Text tweaks
COLOUR_END_TEXT = (0, 0, 0)        # Black for readability
COLOUR_LABEL = (0, 100, 0)         # Dark green for object labels
COLOUR_LABEL_OUTLINE = (255, 255, 255)

# Fun Game Fonts!
FONT_NAME = "comicsansms, segoeprint, arial black, impact"

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
