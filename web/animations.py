import time
import random
import threading

# State machiness
animation_state = {
    "is_running": False,
    "current_name": None,
    "thread": None
}

# Turns off all the LEDs and stops any running animation
def stop_all_animations(pixels, state):
    state["is_running"] = False

    # Wait for animation to finish
    if state["thread"]:
        state["thread"].join()
        state["thread"] = None

    # Turn off all LEDs
    pixels.fill((0, 0, 0))
    pixels.show()

# Creates a rainbow color (returns color in GBR....)
# position should olny be between 0 and 1
# where red is at the top and blue is at the bottom
def make_rainbow_color(position):
    if position < 0.2:
        return (0, 0, 255) # Red
    elif position < 0.4:
        return (127, 0, 255) # Orange
    elif position < 0.6:
        return (255, 0, 255) # Yellow
    elif position < 0.8:
        return (255, 0, 0) # Green
    else:
        return (0, 255, 0) # Blue

# Makes LEDs light up in blue, in a pattern so it looks
# like rain falling
def run_rain_effect(pixels, led_positions, state):
    # Sort LEDs by height
    for i in range(len(led_positions)):
        print(led_positions[i]['y'])

    sorted_leds = sorted(led_positions, key=lambda x: x['y'], reverse=True)
    for j in range(len(sorted_leds)):
        print(sorted_leds[j]['y'])

    while state["is_running"]:
        lit_leds = []

        # Light up LEDs from top to bottom
        for led in sorted_leds:
            if not state["is_running"]:
                break

            # Turn on one LED in blue
            led_id = led['id']
            pixels[led_id] = (0, 255, 0)  # Blue in GBR format
            lit_leds.append(led_id)
            pixels.show()
            time.sleep(0.05)

            # Keep last 3 LEDs lit
            # at the same time
            if len(lit_leds) > 3:
                old_led = lit_leds.pop(0)
                pixels[old_led] = (0, 0, 0)
                pixels.show()

        # Turn off remaining lit LEDs
        for led_id in lit_leds:
            if not state["is_running"]:
                break
            pixels[led_id] = (0, 0, 0)
            pixels.show()
            time.sleep(0.05)

        time.sleep(random.uniform(0.1, 0.5))

# Makes LEDs light up in a spiral pattern
# where the color of the LED depends on its height
def run_spiral_effect(pixels, led_positions, state):
    # Sort LEDs by height
    sorted_leds = sorted(led_positions, key=lambda x: x['y'], reverse=True)
    speed = 0.15 # Lower is faster

    while state["is_running"]:
        pixels.fill((0, 0, 0))
        pixels.show()

        for i, led in enumerate(sorted_leds):
            if not state["is_running"]:
                break

            height_percent = i / len(sorted_leds)
            color = make_rainbow_color(height_percent)

            pixels[led['id']] = color
            pixels.show()
            time.sleep(speed)

        if state["is_running"]:
            time.sleep(1.0)

# Lightning effect
# White flashing
def run_lightning_effect(pixels, led_positions, state):
    sorted_leds = sorted(led_positions, key=lambda x: x['y'], reverse=True)
    
    while state["is_running"]:
        flashes = random.randint(1, 3)
        for _ in range(flashes):
            for led in sorted_leds:
                pixels[led['id']] = (255, 255, 255) # White
            pixels.show()
            
            time.sleep(0.1)
            
            # Turn all LEDs off
            for led in sorted_leds:
                pixels[led['id']] = (0, 0, 0)
            pixels.show()
            
            time.sleep(0.1)
        
        time.sleep(random.uniform(2.0, 5.0))

# Gentle snow effect
# White falling
def run_snow_effect(pixels, led_positions, state):
    sorted_leds = sorted(led_positions, key=lambda x: x['y'], reverse=True)
    
    while state["is_running"]:
        num_snowflakes = random.randint(1, 5)
        lit_leds = []
        
        for _ in range(num_snowflakes):
            if len(sorted_leds) > 0:
                led = random.choice(sorted_leds)
                pixels[led['id']] = (200, 200, 200) # Soft white
                lit_leds.append(led['id'])
                pixels.show()
                
        time.sleep(0.3)
        
        # Turn off snowflakes
        for led_id in lit_leds:
            pixels[led_id] = (0, 0, 0)
        pixels.show()
        
        time.sleep(0.2)

# Gentle sun effect
# Yellow and orange
def run_sun_effect(pixels, led_positions, state):
    sorted_leds = sorted(led_positions, key=lambda x: -x['y'])
    base_color = (200, 100, 0) # Orange/yellow in GBR format
    
    while state["is_running"]:
        for brightness in range(0, 100, 2):
            if not state["is_running"]:
                break
                
            factor = brightness / 100.0
            color = tuple(int(c * factor) for c in base_color)
            
            for led in sorted_leds:
                pixels[led['id']] = color
            pixels.show()
            time.sleep(0.02)
            
        for brightness in range(100, 0, -2):
            if not state["is_running"]:
                break
                
            factor = brightness / 100.0
            color = tuple(int(c * factor) for c in base_color)
            
            for led in sorted_leds:
                pixels[led['id']] = color
            pixels.show()

# Starts the weather animation based on weather type
def start_weather_animation(pixels, led_positions, state, weather_type):
    if state["is_running"]:
        return False
        
    state["is_running"] = True
    state["current_name"] = weather_type
    
    if weather_type == "Rain":
        target = run_rain_effect
    elif weather_type == "Thunderstorm":
        target = run_lightning_effect
    elif weather_type == "Snow":
        target = run_snow_effect
    elif weather_type == "Clear":
        target = run_sun_effect
    else:
        return False

    state["thread"] = threading.Thread(
        target=target,
        args=(pixels, led_positions, state)
    )
    state["thread"].start()
    return True

# Starts the rain animation
def start_rain(pixels, led_positions, state):
    if state["is_running"]:
        return False
        
    state["is_running"] = True
    state["current_name"] = "rain"
    state["thread"] = threading.Thread(
        target=run_rain_effect, 
        args=(pixels, led_positions, state)
    )
    state["thread"].start()
    return True

# Starts the spiral animation
def start_spiral(pixels, led_positions, state):
    if state["is_running"]:
        return False
        
    state["is_running"] = True
    state["current_name"] = "spiral"
    state["thread"] = threading.Thread(
        target=run_spiral_effect, 
        args=(pixels, led_positions, state)
    )
    state["thread"].start()
    return True

# Gets the current color of each LED as hex colors
def get_current_colors(pixels, num_pixels):
    colors = {}
    for i in range(num_pixels):
        color = pixels[i]
        # Convert from GBR to hex RGB color
        hex_color = f'#{color[2]:02x}{color[0]:02x}{color[1]:02x}'
        colors[i] = hex_color
    return colors