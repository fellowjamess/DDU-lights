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
    # Use higher resolution and enable HDR for better light detection
    preview_config = picam2.create_preview_configuration(
        main={"size": (3280, 2464), "format": "RGB888"},
        buffer_count=4,
        controls={"FrameDurationLimits": (100000, 100000),  # Fixed exposure time
                 "ExposureTime": 50000,  # 50ms exposure
                 "AnalogueGain": 1.0}    # Minimum gain for less noise
    )
    picam2.configure(preview_config)
    picam2.start()
    time.sleep(2)  # Wait for camera to stabilize
    return picam2

# NeoPixel setup
pixel_pin = board.D18
num_pixels = 20
ORDER = neopixel.RGB
pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.5, auto_write=False, pixel_order=ORDER
)

def detect_bright_point(frame, min_area=100):
    # Convert to HSV for better LED detection
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # More precise range for green LED detection
    lower_green = np.array([45, 150, 150])  # Tighter green range
    upper_green = np.array([75, 255, 255])  # Upper limit unchanged
    
    # Create mask with multiple thresholds
    mask1 = cv2.inRange(hsv, lower_green, upper_green)
    
    # Additional brightness-based mask
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, bright_mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    
    # Combine masks
    mask = cv2.bitwise_and(mask1, bright_mask)
    
    # Advanced noise reduction
    mask = cv2.GaussianBlur(mask, (5, 5), 0)
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    # Find contours with sub-pixel accuracy
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    
    if contours:
        # Filter contours by area and circularity
        valid_contours = []
        for c in contours:
            area = cv2.contourArea(c)
            if area > min_area:
                perimeter = cv2.arcLength(c, True)
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                if circularity > 0.7:  # Circle has circularity of 1
                    valid_contours.append(c)
        
        if valid_contours:
            # Get the brightest contour
            brightest = max(valid_contours, 
                          key=lambda c: np.mean(frame[cv2.boundingRect(c)[1]:cv2.boundingRect(c)[1]+cv2.boundingRect(c)[3], 
                                                    cv2.boundingRect(c)[0]:cv2.boundingRect(c)[0]+cv2.boundingRect(c)[2]]))
            
            # Use moments for sub-pixel accuracy
            M = cv2.moments(brightest)
            if M["m00"] != 0:
                cx = M["m10"] / M["m00"]
                cy = M["m01"] / M["m00"]
                
                # Refine position using intensity-weighted average
                roi = frame[max(0, int(cy)-5):int(cy)+6, max(0, int(cx)-5):int(cx)+6]
                if roi.size > 0:
                    y_indices, x_indices = np.indices(roi.shape[:2])
                    intensity = np.mean(roi, axis=2)
                    total_intensity = np.sum(intensity)
                    if total_intensity > 0:
                        refined_x = np.sum(x_indices * intensity) / total_intensity + max(0, int(cx)-5)
                        refined_y = np.sum(y_indices * intensity) / total_intensity + max(0, int(cy)-5)
                        return (refined_x, refined_y), brightest
                
                return (cx, cy), brightest
    
    return None, None

def calculate_3d_position(pixel_index, image_point, camera_params):
    if not image_point:
        return None
        
    x, y = image_point
    
    # Camera calibration matrix (update these values based on actual calibration)
    fx = camera_params['focal_length']  # Focal length in x
    fy = camera_params['focal_length']  # Focal length in y
    cx = camera_params['cx']  # Principal point x
    cy = camera_params['cy']  # Principal point y
    
    # Convert to normalized coordinates
    x_normalized = (x - cx) / fx
    y_normalized = (y - cy) / fy
    
    # Calculate depth using improved triangulation
    if abs(x_normalized) > 0.001:  # Avoid division by zero
        depth = camera_params['baseline'] / x_normalized
        
        # Apply depth limits for outlier rejection
        if 0.1 < depth < 2.0:  # Reasonable depth range in meters
            # Calculate world coordinates
            world_x = depth * x_normalized
            world_y = depth * y_normalized
            world_z = depth
            
            return (world_x, world_y, world_z)
    return None

def main():
    # Initialize camera
    camera = setup_camera()
    
    # Updated camera parameters for better accuracy
    camera_params = {
        'focal_length': 3280,  # Based on full resolution
        'baseline': 0.1,       # Update this based on actual measurement
        'cx': 3280 // 2,      # Center of image x
        'cy': 2464 // 2       # Center of image y
    }
    
    # Clear all pixels
    pixels.fill((0, 0, 0))
    pixels.show()
    
    # Initialize arrays for storing coordinates
    valid_indices = []
    valid_positions = []

    # Create necessary folders
    for folder in ['data', 'data2', 'position']:
        if not os.path.exists(folder):
            os.makedirs(folder)
    
    try:
        # First scan
        print("Starting first scan...")
        first_positions = []
        first_indices = []
        
        # Scan each LED from first position
        for i in range(num_pixels):
            # Turn all LEDs off and wait to ensure they're off
            pixels.fill((0, 0, 0))
            pixels.show()
            time.sleep(0.1)  # Wait for LEDs to fully turn off
            
            # Turn on single LED
            pixels[i] = (0, 255, 0)
            pixels.brightness = 1.0
            pixels.show()
            time.sleep(0.35)  # Wait for LED to stabilize
            
            max_attempts = 3
            for attempt in range(max_attempts):
                frame = camera.capture_array()
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                
                lower_green = np.array([40, 100, 100])
                upper_green = np.array([80, 255, 255])
                mask = cv2.inRange(hsv, lower_green, upper_green)
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                if contours:
                    largest = max(contours, key=cv2.contourArea)
                    M = cv2.moments(largest)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        image_point = (cx, cy)
                        
                        position = calculate_3d_position(i, image_point, camera_params)
                        if position:
                            if -10 < position[2] < 10:
                                first_indices.append(i)
                                first_positions.append(position)
                                print(f"LED {i}: Position {position} (First scan)")
                                
                                cv2.circle(frame, image_point, 5, (255, 0, 0), -1)
                                cv2.imwrite(f"data/debug_led_{i}.jpg", frame)
                                break
                
                if attempt < max_attempts - 1:
                    time.sleep(0.1)
            
            # Turn LED off after capture
            pixels[i] = (0, 0, 0)
            pixels.show()
        
        # Wait 5 seconds before second scan
        print("Waiting 5 seconds before second scan...")
        time.sleep(5)
        
        # Second scan
        print("Starting second scan...")
        second_positions = []
        second_indices = []
        
        # Scan each LED from second position
        for i in range(num_pixels):
            # Turn all LEDs off and wait to ensure they're off
            pixels.fill((0, 0, 0))
            pixels.show()
            time.sleep(0.1)  # Wait for LEDs to fully turn off
            
            # Turn on single LED
            pixels[i] = (0, 255, 0)
            pixels.brightness = 1.0
            pixels.show()
            time.sleep(0.35)  # Wait for LED to stabilize
            
            for attempt in range(max_attempts):
                frame = camera.capture_array()
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                mask = cv2.inRange(hsv, lower_green, upper_green)
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                if contours:
                    largest = max(contours, key=cv2.contourArea)
                    M = cv2.moments(largest)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        image_point = (cx, cy)
                        
                        position = calculate_3d_position(i, image_point, camera_params)
                        if position:
                            if -10 < position[2] < 10:
                                second_indices.append(i)
                                second_positions.append(position)
                                print(f"LED {i}: Position {position} (Second scan)")
                                
                                cv2.circle(frame, image_point, 5, (255, 0, 0), -1)
                                cv2.imwrite(f"data2/debug_led_{i}.jpg", frame)
                                break
                
                if attempt < max_attempts - 1:
                    time.sleep(0.1)
            
            # Turn LED off after capture
            pixels[i] = (0, 0, 0)
            pixels.show()
        
        # Calculate final positions using both scans
        for i in range(num_pixels):
            if i in first_indices and i in second_indices:
                first_pos = first_positions[first_indices.index(i)]
                second_pos = second_positions[second_indices.index(i)]
                
                # Average the positions
                final_pos = tuple((a + b) / 2 for a, b in zip(first_pos, second_pos))
                valid_indices.append(i)
                valid_positions.append(final_pos)
                print(f"LED {i}: Final Position {final_pos}")
    
    except KeyboardInterrupt:
        print("Scanning interrupted")
    
    finally:
        # Reset LED strip
        pixels.brightness = 0.5
        pixels.fill((0, 0, 0))
        pixels.show()
        camera.stop()
        
        # Save results
        if valid_indices:
            valid_indices = np.array(valid_indices)
            valid_positions = np.array(valid_positions)
            np.savez("position/led_coordinates.npz", 
                    indices=valid_indices, 
                    positions=valid_positions)
            print(f"Saved {len(valid_indices)} valid LED positions")
            print("Coordinates saved to position/led_coordinates.npz")
        else:
            print("No valid LED positions detected")

if __name__ == "__main__":
    main()