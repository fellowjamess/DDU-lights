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
        buffer_countW=4
    )
    picam2.configure(preview_config)
    picam2.start()
    return picam2

def detect_led_position(frame):
    # Convert to HSV for better LED detection
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Define range for bright LED
    # First is green, second is blue, third is red
    lower = np.array([100, 100, 40])  # Green HSV range
    upper = np.array([255, 255, 80])  # Green HSV range
    
    # Create mask and find contours
    mask = cv2.inRange(hsv, lower, upper)
    
    # Show the mask in a window
    cv2.imshow('Mask View', mask)
    cv2.waitKey(1)  # Update the window
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        largest = max(contours, key=cv2.contourArea)
        M = cv2.moments(largest)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            return (cx, cy)
    return None

def capture_plan(camera, angle_name):
    positions = []
    
    # Turn on all LEDs
    # With white, where first is green, second is blue, third is red
    pixels.fill((255, 255, 255))
    pixels.show()
    
    # Wait for stable image
    time.sleep(1)
    
    # Capture frame
    frame = camera.capture_array()
    
    # Process frame
    led_positions = []
    for i in range(num_pixels):
        # Turn on only one LED
        pixels.fill((0, 0, 0))
        # First is green, second is blue, third is red
        pixels[i] = (0, 255, 0)
        pixels.show()
        time.sleep(0.1)
        
        # Capture and process frame
        frame = camera.capture_array()
        position = detect_led_position(frame)
        
        if position:
            led_positions.append((i, position[0], position[1]))
            # Draw detection on frame
            cv2.circle(frame, position, 5, (0, 0, 255), -1)
    
    # Save annotated frame
    cv2.imwrite(f"plan_{angle_name}.jpg", frame)
    
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