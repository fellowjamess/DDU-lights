import asyncio
import websockets
import json
import board
import neopixel
from collections import defaultdict

# LED strip configuration
pixel_pin = board.D18
num_pixels = 40 # We have 40 LEDs
pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.5, auto_write=False
)

led_states = defaultdict(lambda: '#000000')  # Default color is black

async def connect_to_server():
    uri = "ws://95.179.138.135:80/ws"
    
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print("Connected to server")
                
                # Send current LED states when connecting
                states_message = {
                    "type": "states",
                    "states": led_states
                }
                await websocket.send(json.dumps(states_message))
                
                while True:
                    try:
                        msg = await websocket.recv()
                        command = json.loads(msg)
                        
                        if command['type'] == 'update':
                            led_id = command.get('led')
                            if led_id is None or not isinstance(led_id, int):
                                print(f"Invalid LED ID: {led_id}")
                                continue
                                
                            if led_id < 0 or led_id >= num_pixels:
                                print(f"LED ID out of range: {led_id}")
                                continue
                            
                            # Convert hex color to RGB
                            color = command.get('color', '#000000').lstrip('#')
                            try:
                                r = int(color[0:2], 16)
                                g = int(color[2:4], 16)
                                b = int(color[4:6], 16)
                                
                                # Update LED and store state
                                pixels[led_id] = (g, b, r)  # GBR order
                                pixels.show()
                                led_states[str(led_id)] = '#' + color
                                
                                # Send confirmation
                                await websocket.send(json.dumps({
                                    "type": "status",
                                    "led": led_id,
                                    "color": '#' + color,
                                    "success": True
                                }))
                            except (ValueError, IndexError) as e:
                                print(f"Error processing color: {e}")
                                
                        elif command['type'] == 'get_states':
                            # Send current LED states
                            await websocket.send(json.dumps({
                                "type": "states",
                                "states": led_states
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
        pixels.fill((0, 0, 0))
        pixels.show()