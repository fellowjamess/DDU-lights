import asyncio
import websockets
import json
import board
import neopixel
import requests
from collections import defaultdict
import json
from animations import AnimationController

# LED strip configuration
pixel_pin = board.D18
num_pixels = 40 # We have 40 LEDs
pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.5, auto_write=False
)

# Try to load LED positions from file
try:
    with open('led_positions.json', 'r') as f:
        led_positions = json.load(f)
except:
    led_positions = [{"id": i, "x": 0, "y": 0, "z": i/num_pixels} for i in range(num_pixels)]

# Initialize animation controller
animation_controller = AnimationController(pixels, num_pixels, led_positions)

led_states = defaultdict(lambda: '#000000')  # Default color is black

def get_initial_states():
    """Gets the initial LED states from server via HTTP request"""
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

async def apply_led_state(led_id, color):
    """Apply color to LED"""
    try:
        color = color.lstrip('#')
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        
        pixels[led_id] = (g, b, r)  # GBR order
        pixels.show()
        led_states[str(led_id)] = '#' + color
    except Exception as e:
        print(f"Error applying LED state: {e}")

async def handle_command(command):
    """Handle incoming commands"""
    cmd_type = command.get('type')
    
    if cmd_type == 'update':
        led_id = command.get('led')
        color = command.get('color', '#000000')
        await apply_led_state(led_id, color)
        return True
        
    elif cmd_type == 'animation':
        action = command.get('action')
        name = command.get('name')
        
        if action == 'start':
            if name == 'rain':
                return animation_controller.start_rain()
            elif name == 'spiral':
                return animation_controller.start_spiral()
        elif action == 'stop':
            animation_controller.stop_animation()
            return True
            
    return False

async def connect_to_server():
    uri = "ws://95.179.138.135:80/ws"
    
    while True:
        try:
            # Get and apply initial states before websocket connection
            initial_states = get_initial_states()
            for led_id_str, color in initial_states.items():
                try:
                    led_id = int(led_id_str)
                    await apply_led_state(led_id, color)
                except ValueError:
                    continue

            async with websockets.connect(uri) as websocket:
                print("Connected to server")
                
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
                            "states": animation_controller.get_led_states()
                        }))
                                
                    except json.JSONDecodeError as e:
                        print(f"Invalid JSON received: {e}")
                        continue
                        
        except websockets.ConnectionClosed:
            print("Connection lost, reconnecting...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        # Clear all LEDs on startup
        pixels.fill((0, 0, 0))
        pixels.show()
        
        # Start the websocket client
        asyncio.get_event_loop().run_until_complete(connect_to_server())
    except KeyboardInterrupt:
        # Clear LEDs on exit
        animation_controller.stop_animation()
        pixels.fill((0, 0, 0))
        pixels.show()