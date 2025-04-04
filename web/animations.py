import time
import random
import threading

class AnimationController:
    def __init__(self, pixels, num_pixels, led_positions):
        self.pixels = pixels
        self.num_pixels = num_pixels
        self.led_positions = led_positions
        self.animation_running = False
        self.animation_thread = None
        self.current_animation = None
        
    def stop_animation(self):
        """Stops any running animation"""
        self.animation_running = False
        if self.animation_thread:
            self.animation_thread.join()
            self.animation_thread = None
        self.pixels.fill((0, 0, 0))
        self.pixels.show()

    def start_rain(self):
        """Starts rain animation"""
        if self.animation_running:
            return False
        self.animation_running = True
        self.current_animation = "rain"
        self.animation_thread = threading.Thread(target=self._rain_animation)
        self.animation_thread.start()
        return True

    def _rain_animation(self):
        """Rain animation implementation"""
        # Sort LEDs by height (z coordinate)
        sorted_leds = sorted(self.led_positions, key=lambda x: x['z'])
        
        while self.animation_running:
            active_leds = []
            for led in sorted_leds:
                if not self.animation_running:
                    break
                    
                led_id = led['id']
                self.pixels[led_id] = (0, 255, 0)  # Blue in GBR format
                active_leds.append(led_id)
                self.pixels.show()
                time.sleep(0.05)
                
                if len(active_leds) > 3:
                    old_led = active_leds.pop(0)
                    self.pixels[old_led] = (0, 0, 0)
                    self.pixels.show()
            
            for led_id in active_leds:
                if not self.animation_running:
                    break
                self.pixels[led_id] = (0, 0, 0)
                self.pixels.show()
                time.sleep(0.05)
            
            time.sleep(random.uniform(0.1, 0.5))

    def start_spiral(self):
        """Starts spiral animation"""
        if self.animation_running:
            return False
        self.animation_running = True
        self.current_animation = "spiral"
        self.animation_thread = threading.Thread(target=self._spiral_animation)
        self.animation_thread.start()
        return True

    def _get_rainbow_color(self, position):
        """Get rainbow color based on position (0-1)"""
        if position < 0.2:
            return (0, 0, 255)  # Red (in GBR format)
        elif position < 0.4:
            return (127, 0, 255)  # Orange
        elif position < 0.6:
            return (255, 0, 255)  # Yellow
        elif position < 0.8:
            return (255, 0, 0)  # Green
        else:
            return (0, 255, 0)  # Blue

    def _spiral_animation(self):
        """Spiral animation implementation"""
        sorted_leds = sorted(self.led_positions, key=lambda x: x['z'])
        speed = 0.2
        
        while self.animation_running:
            self.pixels.fill((0, 0, 0))
            self.pixels.show()
            
            for i, led in enumerate(sorted_leds):
                if not self.animation_running:
                    break
                    
                height_position = i / len(sorted_leds)
                color = self._get_rainbow_color(height_position)
                self.pixels[led['id']] = color
                self.pixels.show()
                time.sleep(speed)
            
            if self.animation_running:
                time.sleep(1.0)

    def get_led_states(self):
        """Returns current LED states as hex colors"""
        states = {}
        for i in range(self.num_pixels):
            color = self.pixels[i]
            # Convert GBR to hex RGB
            hex_color = f'#{color[2]:02x}{color[0]:02x}{color[1]:02x}'
            states[i] = hex_color
        return states