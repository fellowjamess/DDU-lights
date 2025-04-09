from scipy.spatial.transform import Rotation
from picamera2 import Picamera2
import numpy as np
import cv2
import time
import sys
import select
import board
import neopixel
import os
import yaml

# NeoPixel setup
pixel_pin = board.D18
num_pixels = 40  # We have 40 LEDs
pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, auto_write=False # Set to False to control when to write to the strip (with pixels.show)
)

def setup_camera():
    picam2 = Picamera2()
    preview_config = picam2.create_preview_configuration(
        main={"size": (1920, 1080)},
        buffer_count=4 # Default is 2, but more frame buffers should reduce frame dropping during capture 
    )
    picam2.configure(preview_config)
    picam2.start()
    return picam2

# Takes a image frame in BGR format,
# index number of the LED,
# name of the angle (alpha or beta)
def detect_led_position(frame, i, angle_name):
    # Convert image from BGR to HSV
    # HSV should be better for detecting specific colors like blue
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define the blue color range that want to find
    # Values are in HSV
    lower_blue = np.array([100, 150, 100])
    upper_blue = np.array([130, 255, 255])

    # Creates a black and white mask where white pixels are blue in the original image
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Mabye move this, so it only runs twice
    # Make folders to save debug images
    mask_folder = os.path.join('data', f'{angle_name}_mask')
    contour_folder = os.path.join('data', f'{angle_name}_contours')
    if not os.path.exists(mask_folder):
        os.makedirs(mask_folder)
    if not os.path.exists(contour_folder):
        os.makedirs(contour_folder)

    # Save the black and white mask image for this LED
    mask_path = os.path.join(mask_folder, f'led_{i}_mask.jpg')
    cv2.imwrite(mask_path, mask)

    # Find the outlines (contours) of white areas in the mask
    # cv2.RETR_EXTERNAL finds only the outermost contours, shuld ignore any holes inside objects
    # cv2.CHAIN_APPROX_SIMPLE compresses the contours to save memory by only storing their corner points
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        # Find the biggest white area, should be the LED (however the LED appears white in the mask, probably due to the camera)
        largest = max(contours, key=cv2.contourArea)
        # Calculate the center point of this area
        M = cv2.moments(largest)

        # Lets not divide by zero
        if M["m00"] != 0:
            # Get the x,y coordinates of the LED center
            # Starts from the top-left corner of the image

            # Gets the sum of the x and y coordinates of all pixels in the contour
            # Divides by the number of pixels to get the average (center) position
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            # Draw the outline and center point on a copy of the original image to debug
            contour_image = frame.copy()
            cv2.drawContours(contour_image, [largest], -1, (0, 0, 255), 2)
            cv2.circle(contour_image, (cx, cy), 5, (0, 0, 255), -1)

            # Save the debug image
            contour_path = os.path.join(contour_folder, f'led_{i}_contour.jpg')
            cv2.imwrite(contour_path, contour_image)

            # Return the LED position
            return (cx, cy)
    # Return None if no LED was found (rally bad)
    return None

# Takes the camera object and the angle name (alpha or beta)
def capture_plan(camera, angle_name):
    # First turn off all LEDs
    pixels.fill((0, 0, 0))
    pixels.show()
    time.sleep(0.2)

    led_positions = []
    # frameRGB = None
    # Use BGR so the color of the image is correct
    frameBGR = None

    for i in range(num_pixels):
        # Just to double-check all LEDs are off
        pixels.fill((0, 0, 0))
        pixels.show()
        time.sleep(0.2)

        # Turn on single LED with blue color (in GBR format..)
        pixels[i] = (0, 255, 0)  # Blue in GBR format (WHY!?? NEOPIXEL WHY!?!???)
        pixels.brightness = 1.0
        pixels.show()
        time.sleep(0.3)

        # Capture and process frame
        frameRGB = camera.capture_array()
        frameBGR = cv2.cvtColor(frameRGB, cv2.COLOR_RGB2BGR)
        position = detect_led_position(frameBGR, i, angle_name)

        # Turn off LED after capture
        pixels[i] = (0, 0, 0)
        pixels.show()

        if position:
            # Store LED ID and x,y coordinates
            led_positions.append((i, position[0], position[1]))
            cv2.circle(frameBGR, position, 5, (0, 0, 255), -1)

    # Save the last frame of the angle in data folder
    # to use in view_plans.py
    if frameBGR is not None:
        cv2.imwrite(f"data/plan_{angle_name}.jpg", frameBGR)

    # Save coordinates in data folder
    np.save(f"data/plan_{angle_name}.npy", np.array(led_positions))

    return led_positions

def load_calibration():
    with open("calibration_matrix.yaml", 'r') as f:
        calibration_data = yaml.load(f)
    mtx = np.array(calibration_data['camera_matrix'])
    dist = np.array(calibration_data['dist_coeff'])
    return mtx, dist

def create_projection_matrices(mtx, dist, R1, t1, R2, t2):
    # P = K[R|t] where K is the camera matrix
    # R1 is identity matrix (no rotation) and t1 is zero (at origin)
    P1 = np.dot(mtx, np.hstack((R1, t1)))

    # R2 is 15-degree rotation and t2 is translation in X direction
    P2 = np.dot(mtx, np.hstack((R2, t2)))

    # Return both projection matrices
    return P1, P2

# See https://stackoverflow.com/questions/55740284/how-to-triangulate-a-point-in-3d-space-given-coordinate-points-in-2-image-and-e
def triangulate_points(points1, points2, P1, P2, mtx, dist):
    # Undistort the points using camera calibration parameters
    # This should remove lens distortion effects from the 2D point coordinates
    points1_undist = cv2.undistortPoints(points1.reshape(-1, 1, 2), mtx, dist)
    points2_undist = cv2.undistortPoints(points2.reshape(-1, 1, 2), mtx, dist)

    # OpenCV's triangulatePoints function can find the 3D coordinates
    # The function returns a 4xN array of homogeneous coordinates (X,Y,Z,W) <-- THIS IS 4D!!
    points_4d = cv2.triangulatePoints(P1, P2, 
                                    points1_undist.reshape(2, -1),
                                    points2_undist.reshape(2, -1))

    # Convert from homogeneous to "normal" 3D coordinates
    # Take first 3 rows (X,Y,Z) and divide by 4th row (W)
    points_3d = points_4d[:3] / points_4d[3]

    # Return Nx3 array of 3D points
    return points_3d

def main():
    # Create data folder if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')

    # Setup camera
    camera = setup_camera()

    # Load calibration
    mtx, dist = load_calibration()

    # Define camera positions and orientations
    # First position (0 degrees - front view)
    R1 = np.eye(3) # No rotation
    t1 = np.zeros((3, 1)) # Origin

    # Second position (15 degrees - side view)
    # Rotate 15 degrees around Y-axis to the right
    # This means you have to rotate the camera to the left to see the same view
    R2 = Rotation.from_euler('y', 15, degrees=True).as_matrix()
    t2 = np.array([[2000], [0], [0]]) # 2000mm/2m translation in X

    # Create projection matrices
    P1, P2 = create_projection_matrices(mtx, dist, R1, t1, R2, t2)

    try:
        # First capture (alpha plan - 0 degrees)
        print("Capturing alpha plan (0 degrees)")
        print("Please ensure the camera is in the initial position")
        input("Press Enter to continue...")
        alpha_positions = capture_plan(camera, "alpha")

        # Wait for the user to press enter and blink LEDs red to indicate rotation
        print("\nPlease rotate camera 15 degrees")
        print("Press Enter when camera is rotated")
        while True:
            # Check if there's input available
            if select.select([sys.stdin], [], [], 0.2)[0]:
                input()
                break

            # Blink LED while waiting
            pixels.fill((0, 0, 255))
            pixels.show()
            time.sleep(0.25)
            pixels.fill((0, 0, 0))
            pixels.show()
            time.sleep(0.25)

        pixels.fill((0, 0, 0))
        pixels.show()
        time.sleep(0.1)

        # Second capture (beta plan - 15 degrees)
        print("Capturing beta plan (15 degrees)")
        beta_positions = capture_plan(camera, "beta")

        # Dictionaries to store positions by LED ID
        alpha_dict = {p[0]: (p[1], p[2]) for p in alpha_positions}
        beta_dict = {p[0]: (p[1], p[2]) for p in beta_positions}

        # Should find common LED IDs, that are detected in both views/plans
        common_leds = set(alpha_dict.keys()) & set(beta_dict.keys())

        if not common_leds:
            print("No LEDs were detected in both views/plans!")
            return

        #  Arrays only for LEDs detected in both views/plans
        points1 = []
        points2 = []
        led_ids = []

        for led_id in common_leds:
            points1.append(alpha_dict[led_id])
            points2.append(beta_dict[led_id])
            led_ids.append(led_id)

        points1 = np.array(points1, dtype=np.float32)
        points2 = np.array(points2, dtype=np.float32)

        print(f"Processing {len(common_leds)} LEDs detected in both views")

        # Triangulate 3D points
        points_3d = triangulate_points(points1, points2, P1, P2, mtx, dist)

        # Save results
        led_positions_3d = {}
        for i, point3d in enumerate(points_3d):
            led_id = led_ids[i]
            led_positions_3d[led_id] = {
                "id": led_id,
                "x": point3d[0],
                "y": point3d[1],
                "z": point3d[2]
            }

        # Save to file with world coordinates
        # Where X, Y, Z are in mm
        with open('data/led_3d_coordinates.txt', 'w') as f:
            f.write("LED ID, X, Y, Z\n")
            for led_id in sorted(led_positions_3d.keys()):
                led = led_positions_3d[led_id]
                print(f"LED {led['id']}: ({led['x']:.4f}, {led['y']:.4f}, {led['z']:.4f})")
                f.write(f"{led['id']},{led['x']:.4f},{led['y']:.4f},{led['z']:.4f}\n")

        # Print missing LEDs
        all_leds = set(range(num_pixels))
        missing_leds = all_leds - common_leds
        if missing_leds:
            print("\nMissing LEDs (not detected in both views):")
            print(sorted(missing_leds))

    except KeyboardInterrupt:
        print("\nCapture interrupted")

    finally:
        # Clean up
        pixels.fill((0, 0, 0))
        pixels.show()
        camera.stop()

if __name__ == "__main__":
    main()
