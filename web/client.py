import asyncio
import websockets
import json
import board
import neopixel
import requests
import json
from collections import defaultdict
from animations import start_rain, start_spiral, stop_all_animations

# LED strip configuration
pixel_pin = board.D18
num_pixels = 40 # We have 40 LEDs
pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=1, auto_write=False
)
led_states = defaultdict(lambda: '#000000')  # Default color is black (aka turned off)

# Animation state like in animations.py
animation_state = {
    "is_running": False,
    "current_name": None,
    "thread": None
}

# Try to load LED positions from file
try:
    led_positions = []
    with open('data/led_3d_coordinates.txt', 'r') as f:
        next(f) # Skip header line which is just "LED ID, X, Y, Z"
        for line in f:
            parts = line.strip().split(',')
            led_positions.append({
                "id": int(parts[0]),
                "x": float(parts[1]),
                "y": float(parts[2]),
                "z": float(parts[3])
            })
except Exception as e:
    print(f"Error loading LED positions: {e}")
    led_positions = []


# Gets the initial LED states from server via HTTP request (not ws, could not get it to work)
# Server returns a dictionary with LED IDs as keys and colors as values.
# Very good example: {"0": "#FF0000", "1": "#00FF00"}
def get_initial_states():
    try:
        response = requests.get('http://95.179.138.135:80/api/getStates')
        if response.status_code == 200:
            states = response.json()
            return states
        else:
            print(f"Error getting states: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error getting initial states: {e}")
        return {}

# Applys color to LED
async def apply_led_state(led_id, color):
    try:
        # Make the hex colors RGB
        color = color.lstrip('#')
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        
        # RGB to GBR....
        pixels[led_id] = (g, b, r)  # GBR order
        pixels.show()
        led_states[str(led_id)] = '#' + color
    except Exception as e:
        print(f"Error applying LED state: {e}")

# Handle incoming commands
async def handle_command(command):
    cmd_type = command.get('type')
    
    if cmd_type == 'update':
        led_id = command.get('led')
        color = command.get('color', '#000000')
        if led_id is not None:
            await apply_led_state(led_id, color)
            return True
    
    elif cmd_type == 'updateAll':
        color = command.get('color', '#000000')
        for i in range(num_pixels):
            await apply_led_state(i, color)
        return True

    elif cmd_type == 'animation':
        action = command.get('action')
        name = command.get('name')
        
        if action == 'start':
            if name == 'rain':
                return start_rain(pixels, led_positions, animation_state)
            elif name == 'spiral':
                return start_spiral(pixels, led_positions, animation_state)
        elif action == 'stop':
            stop_all_animations(pixels, animation_state)
            return True
            
    return False

async def connect_to_server():
    uri = "ws://95.179.138.135:80/ws"
    
    while True:
        try:
            # Use the initial states of the LEDs before websocket connection
            initial_states = get_initial_states()
            for led_id_str, color in initial_states.items():
                try:
                    led_id = int(led_id_str)
                    await apply_led_state(led_id, color)
                except ValueError:
                    continue

            async with websockets.connect(uri) as websocket:
                print("Connected to server")
                
                # Send LED positions
                positions_message = {
                    "type": "positions",
                    "positions": json.dumps(led_positions) if led_positions else "[]"
                }
                await websocket.send(json.dumps(positions_message))

                # Send current LED states to confirm
                states_message = {
                    "type": "states",
                    "states": led_states
                }
                await websocket.send(json.dumps(states_message))

                while True:
                    try:
                        msg = await websocket.recv()
                        command = json.loads(msg)

                        success = await handle_command(command)
                        
                        # Send status update
                        await websocket.send(json.dumps({
                            "type": "status",
                            "success": success,
                            "states": led_states
                        }))
                                
                    except json.JSONDecodeError as e:
                        print(f"Invalid JSON received: {e}")
                        continue

        except websockets.ConnectionClosed:
            print("Connection lost, reconnecting...")
            # Try to connect again after 5 seconds
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        # Clear all LEDs on startup
        pixels.fill((0, 0, 0))
        pixels.show()

        # Start websocket client
        asyncio.get_event_loop().run_until_complete(connect_to_server())
    except KeyboardInterrupt:
        # Clear LEDs on exit
        stop_all_animations(pixels, animation_state)
        pixels.fill((0, 0, 0))
        pixels.show()