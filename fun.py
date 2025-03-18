import board
import neopixel
import time
import argparse
import random
from math import sin, pi

def parse_args():
    parser = argparse.ArgumentParser(description='NeoPixel Fun Patterns')
    parser.add_argument('num_pixels', type=int, help='Number of NeoPixels in your strip')
    parser.add_argument('--brightness', type=float, default=0.5, help='Brightness (0.0-1.0)')
    return parser.parse_args()

def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)

class NeoPixelPatterns:
    def __init__(self, num_pixels, brightness=0.5):
        self.pixels = neopixel.NeoPixel(
            board.D18, num_pixels, brightness=brightness, auto_write=False)
        self.num_pixels = num_pixels

    def rainbow_cycle(self, wait):
        for j in range(255):
            for i in range(self.num_pixels):
                pixel_index = (i * 256 // self.num_pixels) + j
                self.pixels[i] = wheel(pixel_index & 255)
            self.pixels.show()
            time.sleep(wait)

    def bounce(self, color, wait):
        for i in range(self.num_pixels):
            self.pixels.fill((0, 0, 0))
            self.pixels[i] = color
            self.pixels.show()
            time.sleep(wait)
        for i in range(self.num_pixels-1, -1, -1):
            self.pixels.fill((0, 0, 0))
            self.pixels[i] = color
            self.pixels.show()
            time.sleep(wait)

    def wave(self, wait):
        for i in range(360):
            for j in range(self.num_pixels):
                # Create sine wave effect
                r = int((sin(i/30 + j/5) + 1) * 127)
                g = int((sin(i/30 + j/5 + 2*pi/3) + 1) * 127)
                b = int((sin(i/30 + j/5 + 4*pi/3) + 1) * 127)
                self.pixels[j] = (r, g, b)
            self.pixels.show()
            time.sleep(wait)

    def sparkle(self, wait, color=(255, 255, 255)):
        self.pixels.fill((0, 0, 0))
        for _ in range(self.num_pixels // 2):
            i = random.randint(0, self.num_pixels-1)
            self.pixels[i] = color
        self.pixels.show()
        time.sleep(wait)
        self.pixels.fill((0, 0, 0))
        self.pixels.show()

def main():
    args = parse_args()
    np = NeoPixelPatterns(args.num_pixels, args.brightness)

    try:
        while True:
            print("Running rainbow cycle...")
            np.rainbow_cycle(0.01)
            print("Running bounce...")
            np.bounce((255, 0, 0), 0.1)
            print("Running wave...")
            np.wave(0.05)
            print("Running sparkle...")
            np.sparkle(0.1)

    except KeyboardInterrupt:
        print("\nCleaning up...")
        np.pixels.fill((0, 0, 0))
        np.pixels.show()

if __name__ == "__main__":
    main()