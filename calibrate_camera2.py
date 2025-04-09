# This program follows this guide: https://sharad-rawat.medium.com/raspberry-pi-camera-module-calibration-using-opencv-f75ff9fc1441
# and some code is based on or from https://nikatsanka.github.io/camera-calibration-using-opencv-and-python.html

from picamera2 import Picamera2
import numpy as np
import cv2
import time
import yaml
import os

def setup_camera():
    picam2 = Picamera2()
    preview_config = picam2.create_preview_configuration(
        main={"size": (4608, 2592)},
        buffer_count=4
    )
    picam2.configure(preview_config)
    picam2.start()
    return picam2

def capture_calibration_images(camera, num_images=20):
    if not os.path.exists('calibration_images'):
        os.makedirs('calibration_images')
    
    print("Press Enter to capture an image (type 'q' and Enter to finish)")
    count = 0
    
    while count < num_images:
        # Get user input
        user_input = input()
        
        if user_input.lower() == 'q':
            break
            
        if user_input == '':  # Enter key pressed
            frame = camera.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            filename = f'calibration_images/calib_{count}.jpg'
            cv2.imwrite(filename, frame)
            print(f"Saved {filename}")
            count += 1
            
    return count

def calibrate_camera(image_dir='calibration_images', checkerboard=(9,6)):
    objp = np.zeros((checkerboard[0] * checkerboard[1], 3), np.float32)
    objp[:,:2] = np.mgrid[0:checkerboard[0], 0:checkerboard[1]].T.reshape(-1,2)

    # Store object points and image points
    objpoints = []
    imgpoints = []

    # List of calibration images
    images = [os.path.join(image_dir, f) for f in os.listdir(image_dir) if f.endswith('.jpg')]

    print(f"Found {len(images)} calibration images")

    for fname in images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Find chessboard corners
        ret, corners = cv2.findChessboardCorners(gray, checkerboard, None)

        if ret:
            # Refine corner positions
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners2 = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)

            objpoints.append(objp)
            imgpoints.append(corners2)

            # Draw and display corners
            cv2.drawChessboardCorners(img, checkerboard, corners2, ret)
            #cv2.imshow('Corners', cv2.resize(img, (1280, 720)))
            #cv2.waitKey(500)

    cv2.destroyAllWindows()

    if len(objpoints) == 0:
        raise Exception("No valid calibration images found!")

    # Calibrate camera
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, gray.shape[::-1], None, None
    )

    # Save calibration results
    calibration_data = {
        'camera_matrix': mtx.tolist(),
        'dist_coeff': dist.tolist()
    }

    with open('calibration_matrix.yaml', 'w') as f:
        yaml.dump(calibration_data, f)

    print("Calibration complete! Results saved to calibration_matrix.yaml")
    return mtx, dist

def main():
    # Create data directory if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')
        
    # Setup camera
    camera = setup_camera()
    time.sleep(2)
    
    try:
        # First capture calibration images
        num_captured = capture_calibration_images(camera)
        
        if num_captured > 0:
            # Then perform calibration
            mtx, dist = calibrate_camera()
            
            # Print calibration matrix
            print("\nCamera Matrix:")
            print(mtx)
            print("\nDistortion Coefficients:")
            print(dist)
    
    finally:
        camera.stop()

if __name__ == "__main__":
    main()