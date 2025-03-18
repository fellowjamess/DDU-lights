from picamera2 import Picamera2
import cv2
import numpy as np
import time
import board
import neopixel
import os

# Camera setup
def setup_camera():
    picam2 = Picamera2()
    preview_config = picam2.create_preview_configuration(
        main={"size": (1920, 1080)},  # Higher resolution for better accuracy
        buffer_count=4
    )
    picam2.configure(preview_config)
    picam2.start()
    return picam2

# NeoPixel setup
pixel_pin = board.D18
num_pixels = 40
ORDER = neopixel.RGB
pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.5, auto_write=False, pixel_order=ORDER
)

def detect_bright_point(frame):
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Threshold to find bright spot
    _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # Get largest contour
        largest = max(contours, key=cv2.contourArea)
        M = cv2.moments(largest)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            return (cx, cy)
    return None

def calculate_3d_position(pixel_index, image_points, camera_params):
    # Known parameters
    strip_length = 1.0  # Length of LED strip in meters
    pixel_spacing = strip_length / num_pixels
    
    # Calculate LED physical position (simplified)
    led_x = pixel_index * pixel_spacing
    
    # Use camera parameters to calculate 3D position
    if image_points:
        x1, y1 = image_points[0]
        x2, y2 = image_points[1]
        # Simple triangulation (needs calibration for accuracy)
        depth = camera_params['focal_length'] * camera_params['baseline'] / (x1 - camera_params['cx'])
        world_y = (y1 - camera_params['cy']) * depth / camera_params['focal_length']
        return (led_x, world_y, depth)
    return None

def capture_images(camera, folder, num_pixels):
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    for i in range(num_pixels):
        # Turn on single LED with bright green
        pixels.fill((0, 0, 0))
        pixels[i] = (0, 255, 0)  # Changed to pure green
        pixels.brightness = 1.0   # Maximum brightness
        pixels.show()
        
        # Wait for stable image
        time.sleep(0.35)
        
        # Capture frame
        frame = camera.capture_array()
        
        # Convert frame to HSV for better green detection
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Define green color range
        lower_green = np.array([40, 100, 100])
        upper_green = np.array([80, 255, 255])
        
        # Create mask for green pixels
        mask = cv2.inRange(hsv, lower_green, upper_green)
        
        # Find contours in the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Get largest contour
            largest = max(contours, key=cv2.contourArea)
            M = cv2.moments(largest)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                image_point = (cx, cy)
                
                # Save debug image with detection visualization
                cv2.circle(frame, image_point, 5, (255, 0, 0), -1)
                cv2.imwrite(f"{folder}/debug_led_{i}.jpg", frame)

def main():
    # Initialize camera
    camera = setup_camera()
    
    # Camera parameters (needs calibration)
    camera_params = {
        'focal_length': 1000,  # pixels
        'baseline': 0.1,       # meters
        'cx': 640,            # principal point x
        'cy': 360             # principal point y
    }
    
    # Clear all pixels
    pixels.fill((0, 0, 0))
    pixels.show()
    
    # Initialize arrays for storing coordinates
    valid_indices = []
    valid_positions = []

    try:
        # Capture first set of images
        capture_images(camera, 'data', num_pixels)
        
        # Wait for 5 seconds
        time.sleep(5)
        
        # Simulate moving the camera to a different position
        camera_params['cx'] += 10  # Adjust the principal point x for the second set
        
        # Capture second set of images
        capture_images(camera, 'data2', num_pixels)
        
        # Calculate 3D positions using images from both folders
        for i in range(num_pixels):
            image_points = []
            for folder in ['data', 'data2']:
                frame = cv2.imread(f"{folder}/debug_led_{i}.jpg")
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                mask = cv2.inRange(hsv, lower_green, upper_green)
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    largest = max(contours, key=cv2.contourArea)
                    M = cv2.moments(largest)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        image_points.append((cx, cy))
            
            if len(image_points) == 2:
                # Calculate 3D position
                position = calculate_3d_position(i, image_points, camera_params)
                if position:
                    # Validate position
                    if -10 < position[2] < 10:  # depth sanity check
                        valid_indices.append(i)
                        valid_positions.append(position)
                        print(f"LED {i}: Position {position}")
                
    except KeyboardInterrupt:
        print("Scanning interrupted")
    
    finally:
        # Reset LED strip
        pixels.brightness = 0.5  # Reset to original brightness
        pixels.fill((0, 0, 0))
        pixels.show()
        camera.stop()
        
        # Save results
        if valid_indices:
            valid_indices = np.array(valid_indices)
            valid_positions = np.array(valid_positions)
            np.savez("data/led_coordinates.npz", 
                    indices=valid_indices, 
                    positions=valid_positions)
            print(f"Saved {len(valid_indices)} valid LED positions")
            print("Coordinates saved to data/led_coordinates.npz")
        else:
            print("No valid LED positions detected")

if __name__ == "__main__":
    main()