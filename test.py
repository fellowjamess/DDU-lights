# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import neopixel


# On CircuitPlayground Express, and boards with built in status NeoPixel -> board.NEOPIXEL
# Otherwise choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D1
# pixel_pin = board.NEOPIXEL

# On a Raspberry pi, use this instead, not all pins are supported
pixel_pin = board.D18

# The number of NeoPixels
num_pixels = 40 # 40 pixels on the strip

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=1, auto_write=False, pixel_order=ORDER
)


def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b) if ORDER in (neopixel.RGB, neopixel.GRB) else (r, g, b, 0)


def rainbow_cycle(wait):
    for i in range(num_pixels):
        if i == 0:
            pixel_index = (i * 256 // num_pixels)
            pixels[i] = wheel(pixel_index & 255)
        pixels.show()
        time.sleep(wait)


def bounce(color, wait):
    """Bounce effect from end to end."""
    for i in range(num_pixels):
        pixels.fill((0, 0, 0))
        pixels[i] = color
        pixels.show()
        time.sleep(wait)
    for i in range(num_pixels-1, -1, -1):
        pixels.fill((0, 0, 0))
        pixels[i] = color
        pixels.show()
        time.sleep(wait)

def theater_chase(color, wait):
    """Movie theater light style chaser animation."""
    for q in range(3):
        for i in range(0, num_pixels, 3):
            if i + q < num_pixels:
                pixels[i + q] = color
        pixels.show()
        time.sleep(wait)
        for i in range(0, num_pixels, 3):
            if i + q < num_pixels:
                pixels[i + q] = (0, 0, 0)

def color_wipe(color, wait):
    """Wipe color across display a pixel at a time."""
    for i in range(num_pixels):
        pixels[i] = color
        pixels.show()
        time.sleep(wait)

while True:
    # Bouncing red dot
    bounce((255, 0, 0), 0.05)
    
    # Theater chase with blue
    for _ in range(5):
        theater_chase((0, 0, 255), 0.05)
    
    # Color wipe with green
    color_wipe((0, 255, 0), 0.05)
    
    # Rainbow cycle
    rainbow_cycle(0.001)
    
    # Random color burst
    for i in range(num_pixels):
        pixels[i] = wheel(i * 256 // num_pixels)
    pixels.show()
    time.sleep(1)
    
    # Strobe effect
    for _ in range(10):
        #pixels.fill((255, 255, 255))
        pixels.show()
        time.sleep(0.05)
        pixels.fill((0, 0, 0))
        pixels.show()
        time.sleep(0.05)