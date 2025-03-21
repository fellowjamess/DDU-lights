from picamera2 import Picamera2
import cv2
import numpy as np
import time
import board
import neopixel
import os

# NeoPixel setup
pixel_pin = board.D18
num_pixels = 20  # Adjust based on your LED strip
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

def detect_led_position(frame, i, angle_name):
    # Convert to HSV for better LED detection
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # GBR order for NeoPixel
    # Define ranges for red (requires two ranges due to how hue wraps around)
    lower_red1 = np.array([0, 100, 100])    # First red range
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])  # Second red range
    upper_red2 = np.array([180, 255, 255])
    
    # Create masks for red color
    mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
    
    # Combine red masks
    mask = cv2.bitwise_or(mask_red1, mask_red2)
    
    # Create folders if they don't exist
    folder_prefix = 'alpha' if angle_name == 'alpha' else 'beta'
    for folder in [f'{folder_prefix}_mask', f'{folder_prefix}_contours']:
        if not os.path.exists(folder):
            os.makedirs(folder)
    
    # Save mask for each LED
    cv2.imwrite(f"{folder_prefix}_mask/led_{i}_mask.jpg", mask)

    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # Get largest contour
        largest = max(contours, key=cv2.contourArea)
        M = cv2.moments(largest)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            
            # Draw contours on a copy of the frame
            contour_image = frame.copy()
            cv2.drawContours(contour_image, [largest], -1, (0, 255, 0), 2)
            cv2.circle(contour_image, (cx, cy), 5, (0, 0, 255), -1)
            
            # Save the contour image
            cv2.imwrite(f"{folder_prefix}_contours/led_{i}_contour.jpg", contour_image)
            
            return (cx, cy)
    return None

def capture_plan(camera, angle_name):
    # First ensure all LEDs are off
    pixels.fill((0, 0, 0))
    pixels.show()
    time.sleep(0.2)
    
    # Process frame
    led_positions = []
    frameBGR = None
    
    for i in range(num_pixels):
        # Double-check all LEDs are off
        pixels.fill((0, 0, 0))
        pixels.show()
        time.sleep(0.2)
        
        # Turn on single LED with red color
        pixels[i] = (0, 0, 255)  # Red in GBR format
        pixels.brightness = 1.0
        pixels.show()
        time.sleep(0.3)
        
        # Capture and process frame
        frameRGB = camera.capture_array()
        frameBGR = cv2.cvtColor(frameRGB, cv2.COLOR_RGB2BGR)
        position = detect_led_position(frameBGR, i, angle_name)
        
        # Turn off LED immediately after capture
        pixels[i] = (0, 0, 0)
        pixels.show()
        
        if position:
            led_positions.append((i, position[0], position[1]))
            # Draw detection on frame
            cv2.circle(frameBGR, position, 5, (0, 255, 0), -1)
    
    # Save annotated frame
    if frameBGR is not None:
        cv2.imwrite(f"plan_{angle_name}.jpg", frameBGR)
    
    # Save coordinates
    np.save(f"plan_{angle_name}.npy", np.array(led_positions))
    
    return led_positions

def main():
    camera = setup_camera()
    
    try:
        # First capture (alpha plan - 0 degrees)
        print("Capturing alpha plan (0 degrees)")
        print("Please ensure camera is in initial position")
        input("Press Enter to continue...")
        alpha_positions = capture_plan(camera, "alpha")
        
        # Wait for camera rotation
        print("\nPlease rotate camera 90 degrees")
        input("Press Enter when camera is rotated...")
        
        # Second capture (beta plan - 90 degrees)
        print("Capturing beta plan (90 degrees)")
        beta_positions = capture_plan(camera, "beta")
        
        # Print results
        print("\nAlpha plan coordinates:")
        for i, x, y in alpha_positions:
            print(f"LED {i}: ({x}, {y})")
        
        print("\nBeta plan coordinates:")
        for i, x, y in beta_positions:
            print(f"LED {i}: ({x}, {y})")
            
    except KeyboardInterrupt:
        print("\nCapture interrupted")
    
    finally:
        # Clean up
        pixels.fill((0, 0, 0))
        pixels.show()
        camera.stop()

if __name__ == "__main__":
    main()