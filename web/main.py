from flask import Flask, render_template, jsonify, request
import numpy as np
import board
import neopixel
import json
import os
import threading
import time
import random
import librosa


app = Flask(__name__)

beat_animation_running = False
beat_animation_thread = None
current_song_path = None
beat_frames = None

# Global variables for volume visualization
volume_animation_running = False
volume_animation_thread = None
current_audio_path = None

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

@app.route('/upload_music', methods=['POST'])
def upload_music():
    global current_song_path, beat_frames
    
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded"})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"success": False, "message": "No selected file"})
    
    # Ensure upload directory exists
    upload_dir = 'uploads'
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save the file
    filepath = os.path.join(upload_dir, file.filename)
    file.save(filepath)
    
    # Load the audio file and analyze beats
    try:
        y, sr = librosa.load(filepath)
        
        # Detect beats
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        
        # Convert beat frames to times
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        
        current_song_path = filepath
        
        return jsonify({
            "success": True, 
            "tempo": float(tempo),  # Convert numpy.float64 to Python float
            "beat_count": int(len(beat_frames)),  # Convert numpy.int64 to Python int
            "duration": float(librosa.get_duration(y=y, sr=sr))  # Convert to Python float
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

def interpolate_color(color1, color2, factor):
    """Create a smooth gradient between two colors"""
    return tuple(int(color1[i] + (color2[i] - color1[i]) * factor) for i in range(3))

def get_gradient_color(position, volume):
    """Get color from gradient based on height position"""
    # Define base colors in GBR format (NeoPixel order)
    GREEN = (255, 0, 0)      # Bottom
    YELLOW = (255, 255, 0)   # Middle
    RED = (0, 0, 255)        # Top
    
    # Create gradient
    if position < 0.5:
        # Gradient from green to yellow
        color = interpolate_color(GREEN, YELLOW, position * 2)
    else:
        # Gradient from yellow to red
        color = interpolate_color(YELLOW, RED, (position - 0.5) * 2)
    
    # Apply volume-based brightness
    brightness = 0.2 + (volume * 0.8)  # Minimum 20% brightness
    return tuple(int(c * brightness) for c in color)

def beat_animation():
    global animation_running, beat_animation_running, current_song_path
    
    if not current_song_path:
        return
    
    # Load audio file
    y, sr = librosa.load(current_song_path)
    
    # Calculate RMS energy (volume)
    hop_length = 2048
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    rms_normalized = (rms - rms.min()) / (rms.max() - rms.min())
    
    # Sort LEDs by height
    sorted_leds = sorted(led_positions, key=lambda x: x['z'])
    num_leds = len(sorted_leds)
    
    frame_idx = 0
    update_rate = 0.1
    last_update = 0
    
    while beat_animation_running and frame_idx < len(rms):
        current_time = time.time()
        
        if current_time - last_update >= update_rate:
            # Get current volume level and scale it
            volume = min(1.0, rms_normalized[frame_idx] * 1.5)
            
            # Clear all LEDs
            pixels.fill((0, 0, 0))
            
            # Calculate how many LEDs to light based on volume
            leds_to_light = int(volume * num_leds)
            
            # Light LEDs with gradient
            for i in range(leds_to_light):
                # Calculate position in gradient (0 to 1)
                position = i / (num_leds - 1)
                
                # Get color from gradient
                color = get_gradient_color(position, volume)
                
                # Set LED color
                led = sorted_leds[i]
                pixels[led['id']] = color
            
            pixels.show()
            frame_idx += 1
            last_update = current_time
        
        time.sleep(0.01)

@app.route('/start_beat_animation', methods=['POST'])
def start_beat_animation():
    global beat_animation_thread, beat_animation_running
    
    if not current_song_path or beat_frames is None:
        return jsonify({"success": False, "message": "No music uploaded"})
    
    if not beat_animation_running:
        beat_animation_running = True
        beat_animation_thread = threading.Thread(target=beat_animation)
        beat_animation_thread.start()
        return jsonify({"success": True, "message": "Beat animation started"})
    
    return jsonify({"success": False, "message": "Animation already running"})

@app.route('/stop_beat_animation', methods=['POST'])
def stop_beat_animation():
    global beat_animation_running
    
    if beat_animation_running:
        beat_animation_running = False
        # Wait for thread to finish
        if beat_animation_thread:
            beat_animation_thread.join()
        
        # Turn off all LEDs
        pixels.fill((0, 0, 0))
        pixels.show()
        
        return jsonify({"success": True, "message": "Beat animation stopped"})
    
    return jsonify({"success": False, "message": "No animation running"})

def get_led_color(position, volume):
    """Get color based on LED position with volume-based brightness"""
    # Define colors in GBR format (NeoPixel order)
    GREEN = (255, 0, 0)      # Bottom section
    YELLOW = (255, 255, 0)   # Middle section
    RED = (0, 0, 255)        # Top section
    
    if position < 0.33:
        return tuple(int(c * volume) for c in GREEN)
    elif position < 0.66:
        return tuple(int(c * volume) for c in YELLOW)
    else:
        return tuple(int(c * volume) for c in RED)

def volume_animation():
    global volume_animation_running, current_audio_path
    
    if not current_audio_path:
        return
    
    # Load and analyze audio
    y, sr = librosa.load(current_audio_path)
    hop_length = 2048  # Analyze in larger chunks for smoother visualization
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    rms_normalized = (rms - rms.min()) / (rms.max() - rms.min())
    
    # Sort LEDs by height
    sorted_leds = sorted(led_positions, key=lambda x: x['z'])
    num_leds = len(sorted_leds)
    
    frame_idx = 0
    update_rate = 0.1  # Update every 100ms
    last_update = 0
    
    while volume_animation_running and frame_idx < len(rms):
        current_time = time.time()
        
        if current_time - last_update >= update_rate:
            # Get current volume
            volume = min(1.0, rms_normalized[frame_idx] * 1.2)
            
            # Light LEDs based on volume
            pixels.fill((0, 0, 0))
            leds_to_light = int(volume * num_leds)
            
            for i in range(leds_to_light):
                position = i / num_leds
                led = sorted_leds[i]
                color = get_led_color(position, volume)
                pixels[led['id']] = color
            
            pixels.show()
            frame_idx += 1
            last_update = current_time
        
        time.sleep(0.01)

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    global current_audio_path
    
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded"})
    
    file = request.files['file']
    filepath = f"uploads/{file.filename}"
    file.save(filepath)
    current_audio_path = filepath
    
    return jsonify({"success": True})

@app.route('/start_volume_animation')
def start_volume_animation():
    global volume_animation_running, volume_animation_thread
    
    if not volume_animation_running:
        volume_animation_running = True
        volume_animation_thread = threading.Thread(target=volume_animation)
        volume_animation_thread.start()
    
    return jsonify({"success": True})

@app.route('/stop_volume_animation')
def stop_volume_animation():
    global volume_animation_running
    volume_animation_running = False
    return jsonify({"success": True})

def rain_animation():
    global animation_running
    while animation_running:
        # Sort LEDs by height (z coordinate) in ascending order (bottom to top)
        sorted_leds = sorted(led_positions, key=lambda x: x['z'])
        
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
            
            # Turn off previous LED if it's not the top one
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

def get_rainbow_color(position):
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

def spiral_animation():
    global animation_running
    
    # Sort LEDs by height and calculate angles
    leds_with_angles = []
    for led in led_positions:
        angle = np.arctan2(led['y'], led['x'])
        height = led['z']
        leds_with_angles.append({
            'id': led['id'],
            'angle': angle,
            'height': height
        })
    
    # Sort by height, then angle
    sorted_leds = sorted(leds_with_angles, key=lambda x: (x['height'], x['angle']))
    num_leds = len(sorted_leds)
    
    # Animation parameters
    speed = 0.15        # Increased delay between frames (slower)
    fade_length = 1.5   # Longer fade trail
    
    while animation_running:
        # Create spiral wave
        for i in range(int(num_leds * fade_length)):
            if not animation_running:
                break
                
            # Clear all LEDs
            pixels.fill((0, 0, 0))
            
            # Light up LEDs in spiral pattern
            for j in range(num_leds):
                # Calculate position in wave (0-1)
                pos = (i + j) % int(num_leds * fade_length)
                fade = 1.0 - (pos / (num_leds * fade_length))
                
                if fade > 0:
                    # Get rainbow color and apply fade
                    color = get_rainbow_color(j / num_leds)
                    color = tuple(int(c * fade) for c in color)
                    pixels[sorted_leds[j]['id']] = color
            
            pixels.show()
            time.sleep(speed)  # Slower animation speed

@app.route('/animation/start_spiral', methods=['POST'])
def start_spiral():
    global animation_thread, animation_running
    if not animation_running:
        animation_running = True
        animation_thread = threading.Thread(target=spiral_animation)
        animation_thread.start()
        return jsonify({"success": True, "message": "Spiral animation started"})
    return jsonify({"success": False, "message": "Animation already running"})

@app.route('/animation/stop_spiral', methods=['POST'])
def stop_spiral():
    global animation_running
    if animation_running:
        animation_running = False
        if animation_thread:
            animation_thread.join()
        pixels.fill((0, 0, 0))
        pixels.show()
        return jsonify({"success": True, "message": "Spiral animation stopped"})
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