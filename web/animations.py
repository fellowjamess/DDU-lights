import time
import random
import threading

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