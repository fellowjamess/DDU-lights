from flask import Flask, render_template, jsonify, request
import numpy as np
import board
import neopixel
import json
import os
import threading
import time
import random

app = Flask(__name__)

# NeoPixel setup
pixel_pin = board.D18
num_pixels = 40
pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.5, auto_write=False
)

# Load LED positions from saved data
try:
    # Get parent directory path
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    coord_file = os.path.join(parent_dir, 'data/led_3d_coordinates.txt')
    
    # Read coordinates from file
    with open(coord_file, 'r') as f:
        lines = f.readlines()[1:]  # Skip header line
    
    led_positions = []
    for line in lines:
        try:
            # Parse line like "LED 0: (1.23, 4.56, 7.89)"
            parts = line.split(':')
            led_id = int(parts[0].replace('LED', '').strip())
            
            # Extract coordinates from parentheses and split
            coords = parts[1].strip()[1:-1].split(',')  # Remove () and split
            x = float(coords[0].strip())
            y = float(coords[1].strip())
            z = float(coords[2].strip())
            
            led_positions.append({
                "id": led_id,
                "x": x,
                "y": y,
                "z": z
            })
        except (ValueError, IndexError) as e:
            print(f"Error parsing line '{line}': {e}")
            continue
            
except Exception as e:
    print(f"Error loading LED coordinates: {e}")
    led_positions = []  # Fallback if no position data exists

print(led_positions)

animation_thread = None
animation_running = False

@app.route('/')
def home():
    return render_template('index.html', led_positions=json.dumps(led_positions))

@app.route('/update_led', methods=['POST'])
def update_led():
    data = request.json
    led_id = data.get('id')
    color = data.get('color', '#000000').lstrip('#')
    
    # Convert hex color to RGB first, then rearrange to GBR
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    gbr = (g, b, r)  # Rearrange to GBR order

    try:
        pixels[led_id] = gbr
        pixels.show()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/update_all', methods=['POST'])
def update_all():
    data = request.json
    color = data.get('color', '#000000').lstrip('#')
    
    # Convert hex color to RGB first, then rearrange to GBR
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    gbr = (g, b, r)  # Rearrange to GBR order
    
    try:
        pixels.fill(gbr)
        pixels.show()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

def rain_animation():
    global animation_running
    while animation_running:
        # Sort LEDs by height (z coordinate)
        sorted_leds = sorted(led_positions, key=lambda x: x['z'], reverse=True)
        
        # Create rain drop
        active_leds = []
        for led in sorted_leds:
            # Add new drop
            led_id = led['id']
            # Blue color in GBR format for NeoPixels
            pixels[led_id] = (0, 255, 0)
            active_leds.append(led_id)
            pixels.show()
            
            # Wait a bit
            time.sleep(0.05)
            
            # Turn off previous LED if it's not the bottom one
            if len(active_leds) > 3:  # Keep 3 LEDs lit as trail
                old_led = active_leds.pop(0)
                pixels[old_led] = (0, 0, 0)
                pixels.show()
        
        # Turn off remaining LEDs
        for led_id in active_leds:
            pixels[led_id] = (0, 0, 0)
            pixels.show()
            time.sleep(0.05)
        
        # Small pause between drops
        time.sleep(random.uniform(0.1, 0.5))

@app.route('/animation/start_rain', methods=['POST'])
def start_rain():
    global animation_thread, animation_running
    if not animation_running:
        animation_running = True
        animation_thread = threading.Thread(target=rain_animation)
        animation_thread.start()
        return jsonify({"success": True, "message": "Rain animation started"})
    return jsonify({"success": False, "message": "Animation already running"})

@app.route('/animation/stop_rain', methods=['POST'])
def stop_rain():
    global animation_running
    if animation_running:
        animation_running = False
        # Wait for thread to finish
        if animation_thread:
            animation_thread.join()
        # Turn off all LEDs
        pixels.fill((0, 0, 0))
        pixels.show()
        return jsonify({"success": True, "message": "Rain animation stopped"})
    return jsonify({"success": False, "message": "No animation running"})

@app.route('/get_led_states', methods=['GET'])
def get_led_states():
    # Return current LED states for 3D view sync
    led_states = {}
    for led in led_positions:
        led_id = led['id']
        color = pixels[led_id]
        # Convert GBR to hex RGB
        hex_color = f'#{color[2]:02x}{color[0]:02x}{color[1]:02x}'
        led_states[led_id] = hex_color
    return jsonify(led_states)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)