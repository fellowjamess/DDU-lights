from picamera2 import Picamera2
import cv2
import numpy as np
import time
import board
import neopixel
import os

# NeoPixel setup
pixel_pin = board.D18
num_pixels = 40  # Adjust based on your LED strip
pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.5, auto_write=False
)

def setup_camera():
    picam2 = Picamera2()
    preview_config = picam2.create_preview_configuration(
        main={"size": (1920, 1080)},
        buffer_count=4
    )
    picam2.configure(preview_config)
    picam2.start()
    return picam2

def detect_led(frame):
    # Convert to HSV for better LED detection
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Define range for bright LED
    lower = np.array([35, 50, 200])  # More permissive bounds
    upper = np.array([85, 255, 255])
    
    # Create mask
    mask = cv2.inRange(hsv, lower, upper)
    
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # Get largest contour
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) > 50:  # Minimum area threshold
            M = cv2.moments(largest)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                return (cx, cy)
    return None

def calculate_3d_position(pixel_index, image_point, camera_params):
    # Known parameters
    strip_length = 1.0  # Length of LED strip in meters
    pixel_spacing = strip_length / num_pixels
    
    # Calculate LED physical position
    led_x = pixel_index * pixel_spacing
    
    if image_point:
        x, y = image_point
        # Simple triangulation
        depth = camera_params['focal_length'] * camera_params['baseline'] / (x - camera_params['cx'])
        world_y = (y - camera_params['cy']) * depth / camera_params['focal_length']
        return (led_x, world_y, depth)
    return None

def main():
    # Create output directory
    output_dir = "xmas_light_position"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    camera = setup_camera()
    
    # Camera parameters (adjust these based on calibration)
    camera_params = {
        'focal_length': 1000,  # pixels
        'baseline': 0.1,       # meters
        'cx': 960,            # principal point x (center of image)
        'cy': 540             # principal point y (center of image)
    }
    
    # Lists to store LED positions
    led_positions = []
    led_indices = []
    
    try:
        # Turn off all LEDs initially
        pixels.fill((0, 0, 0))
        pixels.show()
        time.sleep(0.5)
        
        print("Starting LED position detection...")
        
        # Scan each LED
        for i in range(num_pixels):
            print(f"Processing LED {i}")
            
            # Turn on single LED
            pixels.fill((0, 0, 0))
            pixels[i] = (0, 255, 0)  # Green color
            pixels.brightness = 1.0
            pixels.show()
            time.sleep(0.3)  # Wait for LED to stabilize
            
            # Capture multiple frames and average position
            positions = []
            for _ in range(3):
                frame = camera.capture_array()
                position = detect_led(frame)
                if position:
                    positions.append(position)
                time.sleep(0.1)
            
            # Calculate average position if we got any valid detections
            if positions:
                avg_x = sum(p[0] for p in positions) / len(positions)
                avg_y = sum(p[1] for p in positions) / len(positions)
                image_point = (int(avg_x), int(avg_y))
                
                # Calculate 3D position
                position_3d = calculate_3d_position(i, image_point, camera_params)
                if position_3d:
                    led_indices.append(i)
                    led_positions.append(position_3d)
                    
                    # Save debug image
                    cv2.circle(frame, image_point, 5, (0, 0, 255), -1)
                    cv2.imwrite(f"{output_dir}/led_{i}_debug.jpg", frame)
                    print(f"LED {i}: Position {position_3d}")
            
            # Turn off LED
            pixels[i] = (0, 0, 0)
            pixels.show()
            
    except KeyboardInterrupt:
        print("\nDetection interrupted by user")
    
    finally:
        # Clean up
        pixels.fill((0, 0, 0))
        pixels.show()
        camera.stop()
        
        # Save results if we got any
        if led_positions:
            # Save positions to NPZ file
            np.savez(f"{output_dir}/led_positions.npz",
                    indices=np.array(led_indices),
                    positions=np.array(led_positions))
            
            # Save human-readable positions to text file
            with open(f"{output_dir}/led_positions.txt", 'w') as f:
                f.write("LED ID, X, Y, Z\n")
                for idx, pos in zip(led_indices, led_positions):
                    f.write(f"LED {idx}: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})\n")
            
            print(f"\nSaved {len(led_positions)} LED positions to {output_dir}/")
        else:
            print("\nNo LED positions were detected")

if __name__ == "__main__":
    main()