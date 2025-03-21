from flask import Flask, render_template, jsonify, request
import numpy as np
import board
import neopixel
import json
import os

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
    coord_file = os.path.join(parent_dir, 'led_3d_coordinates.txt')
    
    # Read coordinates from file
    with open(coord_file, 'r') as f:
        lines = f.readlines()
    
    led_positions = []
    for idx, line in enumerate(lines):
        x, y, z = map(float, line.strip().split(','))
        led_positions.append({
            "id": idx,
            "x": x,
            "y": y,
            "z": z
        })
except Exception as e:
    print(f"Error loading LED coordinates: {e}")
    led_positions = []  # Fallback if no position data exists

@app.route('/')
def home():
    return render_template('index.html', led_positions=json.dumps(led_positions))

@app.route('/update_led', methods=['POST'])
def update_led():
    data = request.json
    led_id = data.get('id')
    color = data.get('color', '#000000').lstrip('#')
    
    # Convert hex color to RGB
    rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    
    try:
        pixels[led_id] = rgb
        pixels.show()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/update_all', methods=['POST'])
def update_all():
    data = request.json
    color = data.get('color', '#000000').lstrip('#')
    rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    
    try:
        pixels.fill(rgb)
        pixels.show()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)