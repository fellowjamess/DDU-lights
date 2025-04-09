import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation
import cv2
import yaml

def load_calibration():
    with open("calibration_matrix.yaml", 'r') as f:
        calibration_data = yaml.safe_load(f)
    mtx = np.array(calibration_data['camera_matrix'])
    dist = np.array(calibration_data['dist_coeff'])
    return mtx, dist

def create_projection_matrices(mtx, R1, t1, R2, t2):
    # First camera projection matrix
    P1 = np.dot(mtx, np.hstack((R1, t1)))

    # Second camera projection matrix
    P2 = np.dot(mtx, np.hstack((R2, t2)))

    return P1, P2

def triangulate_points(points1, points2, P1, P2, mtx, dist):
    # Undistort points using camera calibration
    points1_undist = cv2.undistortPoints(points1.reshape(-1, 1, 2), mtx, dist)
    points2_undist = cv2.undistortPoints(points2.reshape(-1, 1, 2), mtx, dist)

    # Triangulate
    points_4d = cv2.triangulatePoints(P1, P2, 
                                    points1_undist.reshape(2, -1),
                                    points2_undist.reshape(2, -1))

    # Convert from homogeneous coordinates to 3D
    points_3d = points_4d[:3] / points_4d[3]
    return points_3d.T

def setup_2d_views(ax1, ax2, alpha_dict, beta_dict, common_leds):
    views = [
        ('alpha', ax1, alpha_dict, 'Front (Alpha)'),
        ('beta', ax2, beta_dict, 'Side (Beta)')
    ]

    for view_name, ax, positions_dict, title in views:
        # Set up view with image or black background
        try:
            img = cv2.imread(f'data/plan_{view_name}.jpg')
            if img is not None:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                ax.imshow(img)
        except:
            ax.set_facecolor('black')

        # Draw LEDs and labels
        for led_id in positions_dict.keys():
            pos = positions_dict[led_id]
            color = 'blue' if led_id in common_leds else 'gray'
            ax.scatter(pos[0], pos[1], color=color, s=50)
            ax.text(pos[0], pos[1], f'{led_id}')

        ax.set_title(title)

        # Set origin to top-left
        ax.set_xlim([0, 1920])
        ax.set_ylim([1080, 0]) # Match image coordinates
        ax.set_title(title)

def main():
    # Load camera calibration
    mtx, dist = load_calibration()

    # Define camera positions and orientations
    R1 = np.eye(3) # No rotation for front view
    t1 = np.zeros((3, 1)) # Origin

    # 15 degree rotation for side view
    R2 = Rotation.from_euler('y', 15, degrees=True).as_matrix()
    t2 = np.array([[2000], [0], [0]]) # 2000mm/2m translation in X

    # Create projection matrices
    P1, P2 = create_projection_matrices(mtx, R1, t1, R2, t2)

    try:
        alpha_positions = np.load('data/plan_alpha.npy')
        beta_positions = np.load('data/plan_beta.npy')
    except FileNotFoundError:
        print("Error: Could not find plan data files. Run capture_plans.py first (or set_up_lights.py).")
        return

    # Create dictionaries to store positions by LED ID
    alpha_dict = {int(p[0]): (p[1], p[2]) for p in alpha_positions}
    beta_dict = {int(p[0]): (p[1], p[2]) for p in beta_positions}

    # Find common LED IDs
    common_leds = set(alpha_dict.keys()) & set(beta_dict.keys())

    if not common_leds:
        print("No LEDs were detected in both views!")
        return

    # Create a new window
    # width=15, height=5
    fig = plt.figure(figsize=(15, 5))

    # Split the window into the 3 diffent views
    ax1 = fig.add_subplot(131)  # Left, alpha view
    ax2 = fig.add_subplot(132)  # Middle, beta view
    ax3 = fig.add_subplot(133, projection='3d')  # Right, 3D view

    # Set up the 2D views
    setup_2d_views(ax1, ax2, alpha_dict, beta_dict, common_leds)

    # Prepare points for triangulation
    points1 = []
    points2 = []
    led_ids = []

    for led_id in sorted(common_leds):
        points1.append(alpha_dict[led_id])
        points2.append(beta_dict[led_id])
        led_ids.append(led_id)

    points1 = np.array(points1, dtype=np.float32)
    points2 = np.array(points2, dtype=np.float32)

    # Triangulate 3D points
    points_3d = triangulate_points(points1, points2, P1, P2, mtx, dist)

    # Store and visualize 3D positions
    led_positions_3d = {}
    x_coords = []
    y_coords = []
    z_coords = []

    for i, point3d in enumerate(points_3d):
        led_id = led_ids[i]
        led_positions_3d[led_id] = {
            "id": led_id,
            "x": point3d[0],
            "y": point3d[1],
            "z": point3d[2]
        }

        # Coordinates for scaling
        x_coords.append(point3d[0])
        y_coords.append(point3d[1])
        z_coords.append(point3d[2])

        # Plot point in 3D
        ax3.scatter(point3d[0], point3d[1], point3d[2], color='blue', s=100)
        ax3.text(point3d[0], point3d[1], point3d[2], f'{led_id}')

    # Calculate bounds for scaling
    padding = 0.1
    x_min, x_max = min(x_coords), max(x_coords)
    y_min, y_max = min(y_coords), max(y_coords)
    z_min, z_max = min(z_coords), max(z_coords)
    x_range = (x_max - x_min) * (1 + padding)
    y_range = (y_max - y_min) * (1 + padding)
    z_range = (z_max - z_min) * (1 + padding)
    x_mid = (x_max + x_min) / 2
    y_mid = (y_max + y_min) / 2
    z_mid = (z_max + z_min) / 2

    # Set axis limits centered around the points
    ax3.set_xlim([x_mid - x_range/2, x_mid + x_range/2])
    ax3.set_ylim([y_mid - y_range/2, y_mid + y_range/2])
    ax3.set_zlim([z_mid - z_range/2, z_mid + z_range/2])

    # Change camera planes
    xx, zz = np.meshgrid([y_mid - y_range/2, y_mid + y_range/2], 
                        [z_mid - z_range/2, z_mid + z_range/2])

    # Add front view plane (red)
    ax3.plot_surface(np.full_like(xx, x_min), xx, zz, 
                    alpha=0.2, color='red')

    # Add side view plane (green)
    ax3.plot_surface(xx, np.full_like(xx, y_min), zz, 
                    alpha=0.2, color='green')

    # Add axies labels for 3D view
    ax3.set_xlabel('X (mm)')
    ax3.set_ylabel('Y (mm)')
    ax3.set_zlabel('Z (mm)')
    ax3.set_title('3D')

    #ax3.view_init(elev=20, azim=45)

    # Print statistics
    print(f"\nTotal LEDs detected in alpha view: {len(alpha_dict)}")
    print(f"Total LEDs detected in beta view: {len(beta_dict)}")
    print(f"LEDs detected in both views: {len(common_leds)}")

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()