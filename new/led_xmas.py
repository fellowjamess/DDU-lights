import cv2
import numpy as np
from picamera2 import Picamera2
import time
from pathlib import Path
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Add these constants at the top of the file
TOTAL_LEDS = 20
DETECTION_THRESHOLD = 180  # Lowered for LED strips
MIN_LED_AREA = 5  # Smaller area for LED strip lights

def setup_camera():
    camera = Picamera2()
    config = camera.create_still_configuration()
    camera.configure(config)
    camera.start()
    time.sleep(2)  # Warm-up time
    return camera

def capture_images(camera, num_angles=4):
    """Capture images from different angles"""
    images = []
    for i in range(num_angles):
        print(f"Please rotate the tree approximately {360//num_angles} degrees")
        input("Press Enter when ready to take photo...")
        
        # Capture image
        image = camera.capture_array()
        images.append(image)
        print(f"Captured image {i+1}/{num_angles}")
        time.sleep(1)
    
    return images

def detect_leds(image, max_leds=TOTAL_LEDS):
    """Detect bright spots (LEDs) in the image"""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)  # Reduced kernel size
    
    # Threshold the image to identify bright spots
    _, binary = cv2.threshold(blurred, DETECTION_THRESHOLD, 255, cv2.THRESH_BINARY)
    
    # Find contours of bright spots
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Sort contours by brightness (area as proxy)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    
    # Get centroids of detected LEDs
    led_positions = []
    for contour in contours[:max_leds]:  # Limit to expected number of LEDs
        if cv2.contourArea(contour) > MIN_LED_AREA:
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                led_positions.append((cx, cy))
    
    return led_positions

def visualize_leds(all_leds, output_dir):
    """Create a 3D visualization of LED positions"""
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Convert 2D positions to approximate 3D positions
    for angle_idx, leds in enumerate(all_leds):
        angle = (angle_idx * 360 / len(all_leds)) * np.pi / 180
        for x, y in leds:
            # Convert to cylindrical coordinates
            r = x / 100  # Scale factor for radius
            z = y / 100  # Scale factor for height
            # Convert to 3D coordinates
            x3d = r * np.cos(angle)
            y3d = r * np.sin(angle)
            ax.scatter(x3d, y3d, z, c='red', marker='o')

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('3D LED Positions on Christmas Tree')
    
    # Save the plot
    plt.savefig(str(output_dir / 'led_visualization_3d.png'))
    plt.close()

def main():
    # Create output directory
    output_dir = Path("tree_images")
    output_dir.mkdir(exist_ok=True)
    
    # Initialize camera
    camera = setup_camera()
    
    # Capture images from different angles
    print("We'll take photos from 4 different angles of the tree")
    images = capture_images(camera, num_angles=4)
    
    # Process each image
    all_leds = []
    for i, image in enumerate(images):
        # Save original image
        cv2.imwrite(str(output_dir / f"tree_angle_{i+1}.jpg"), image)
        
        # Detect LEDs
        led_positions = detect_leds(image)
        if len(led_positions) < TOTAL_LEDS:
            print(f"Warning: Only found {len(led_positions)} LEDs in image {i+1}")
            print("Try adjusting DETECTION_THRESHOLD if too few LEDs are detected")
        elif len(led_positions) > TOTAL_LEDS:
            print(f"Warning: Found {len(led_positions)} LEDs in image {i+1}")
            print("Extra detections will be filtered")
            led_positions = led_positions[:TOTAL_LEDS]
        all_leds.append(led_positions)
        
        # Draw detected LEDs on image
        marked_image = image.copy()
        for x, y in led_positions:
            cv2.circle(marked_image, (x, y), 5, (0, 255, 0), -1)
        
        # Save marked image
        cv2.imwrite(str(output_dir / f"tree_angle_{i+1}_detected.jpg"), marked_image)
        print(f"Found {len(led_positions)} LEDs in image {i+1}")
    
    # Calculate total unique LEDs (approximate)
    total_leds = sum(len(leds) for leds in all_leds)
    print(f"\nTotal LEDs detected across all angles: {total_leds}")
    print(f"Images saved in: {output_dir.absolute()}")
    
    # Visualize LEDs in 3D
    visualize_leds(all_leds, output_dir)
    print("3D visualization saved as 'led_visualization_3d.png'")
    
    camera.stop()

if __name__ == "__main__":
    main()