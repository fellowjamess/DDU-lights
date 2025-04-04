import asyncio
import websockets
import json
import board
import neopixel

# LED strip configuration
pixel_pin = board.D18
num_pixels = 40 # We have 40 LEDs in total
pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.5, auto_write=False
)

async def connect_to_server():
    uri = "ws://95.179.138.135:80/ws" # IP address and port of the server
    
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print("Connected to server")
                
                while True:
                    msg = await websocket.recv()
                    command = json.loads(msg)
                    
                    if command['type'] == 'update':
                        # Convert hex color to RGB
                        color = command['color'].lstrip('#')
                        r = int(color[0:2], 16)
                        g = int(color[2:4], 16)
                        b = int(color[4:6], 16)
                        
                        # Update LED
                        pixels[command['led']] = (g, b, r)  # GBR order
                        pixels.show()
                        
                        # Send back confirmation
                        await websocket.send(json.dumps({
                            "type": "status",
                            "led": command['led'],
                            "color": command['color']
                        }))
                        
        except websockets.ConnectionClosed:
            print("Connection lost, reconnecting...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(connect_to_server())