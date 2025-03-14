import board
import neopixel
import time
import argparse
import random
from math import sin, pi
import pyaudio
import numpy as np
import wave
import struct

# Add these constants for audio processing
CHUNK = 1024  # Audio chunks size
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100  # Audio sampling rate

def parse_args():
    parser = argparse.ArgumentParser(description='NeoPixel Fun Patterns')
    parser.add_argument('num_pixels', type=int, help='Number of NeoPixels in your strip')
    parser.add_argument('--brightness', type=float, default=0.5, help='Brightness (0.0-1.0)')
    parser.add_argument('--audio-file', type=str, help='Path to .wav file (optional)')
    parser.add_argument('--input-device', type=int, help='Audio input device index (optional)')
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

class AudioProcessor:
    def __init__(self, audio_file=None, input_device=None):
        self.p = pyaudio.PyAudio()
        
        if audio_file:
            # File input mode
            self.wave_file = wave.open(audio_file, 'rb')
            self.mode = 'file'
        else:
            # Microphone input mode
            if input_device is None:
                # List available input devices
                print("\nAvailable audio input devices:")
                for i in range(self.p.get_device_count()):
                    dev = self.p.get_device_info_by_index(i)
                    if dev['maxInputChannels'] > 0:
                        print(f"Index {i}: {dev['name']}")
                input_device = int(input("Select input device index: "))
            
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                input=True,
                input_device_index=input_device,
                frames_per_buffer=1024
            )
            self.mode = 'mic'

    def get_audio_data(self):
        if self.mode == 'file':
            data = self.wave_file.readframes(1024)
            if not data:
                self.wave_file.rewind()
                data = self.wave_file.readframes(1024)
        else:
            data = self.stream.read(1024, exception_on_overflow=False)

        # Convert audio data to frequencies
        data_int = struct.unpack(str(len(data)//2) + 'h', data)
        return np.average(np.abs(np.fft.fft(data_int)))

    def __del__(self):
        if self.mode == 'file':
            self.wave_file.close()
        else:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

class NeoPixelPatterns:
    def __init__(self, num_pixels, brightness=0.5, audio_file=None, input_device=None):
        self.pixels = neopixel.NeoPixel(
            board.D18, num_pixels, brightness=brightness, auto_write=False)
        self.num_pixels = num_pixels
        self.audio = AudioProcessor(audio_file, input_device)

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

    # Add this new method for music visualization
    def music_reactive(self, sensitivity=50):
        # Get audio data
        amplitude = self.audio.get_audio_data()
        
        # Map amplitude to number of pixels to light
        num_pixels_to_light = int(min(amplitude / sensitivity, self.num_pixels))
        
        # Create gradient colors based on amplitude
        for i in range(self.num_pixels):
            if i < num_pixels_to_light:
                # Create color gradient from blue to red based on amplitude
                intensity = int((i / self.num_pixels) * 255)
                self.pixels[i] = (intensity, 0, 255 - intensity)
            else:
                self.pixels[i] = (0, 0, 0)
        
        self.pixels.show()

def main():
    args = parse_args()
    np = NeoPixelPatterns(args.num_pixels, args.brightness, args.audio_file, args.input_device)

    try:
        while True:
            print("Music reactive mode...")
            while True:
                np.music_reactive()
                time.sleep(0.01)  # Small delay to prevent overwhelming the LEDs

    except KeyboardInterrupt:
        print("\nCleaning up...")
        np.pixels.fill((0, 0, 0))
        np.pixels.show()

if __name__ == "__main__":
    main()