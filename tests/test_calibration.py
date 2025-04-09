import numpy as np
import yaml
import os

def create_calibration():
    if not os.path.exists('data'):
        os.makedirs('data')

    # Camera matrix for 1920x1080 resolution
    camera_matrix = np.array([
        [1000.0, 0.0, 960.0], # fx, 0, cx
        [0.0, 1000.0, 540.0], # 0, fy, cy
        [0.0, 0.0, 1.0]       # 0, 0, 1
    ])

    # Distortion coefficient
    dist_coeff = np.array([0.0, 0.0, 0.0, 0.0, 0.0])

    # Save calibration data
    calibration_data = {
        'camera_matrix': camera_matrix.tolist(),
        'dist_coeff': dist_coeff.tolist()
    }

    with open("data/calibration_matrix.yaml", "w") as f:
        yaml.dump(calibration_data, f)

if __name__ == "__main__":
    create_calibration()