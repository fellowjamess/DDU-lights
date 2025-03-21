import numpy as np
import matplotlib.pyplot as plt
import cv2
from mpl_toolkits.mplot3d import Axes3D

def main():
    # Load the coordinate data from data folder
    try:
        alpha_positions = np.load('data/plan_alpha.npy')
        beta_positions = np.load('data/plan_beta.npy')
    except FileNotFoundError:
        print("Error: Could not find plan data files. Run plan.py first.")
        return

    # Create figure with three subplots: two 2D views and one 3D view
    fig = plt.figure(figsize=(15, 5))
    
    # 2D Views (original)
    ax1 = fig.add_subplot(131)
    ax2 = fig.add_subplot(132)
    # 3D View
    ax3 = fig.add_subplot(133, projection='3d')

    # Plot alpha plan (0 degrees)
    try:
        img_alpha = cv2.imread('data/plan_alpha.jpg')
        if img_alpha is not None:
            img_alpha = cv2.cvtColor(img_alpha, cv2.COLOR_BGR2RGB)
            ax1.imshow(img_alpha)
    except:
        ax1.set_facecolor('black')

    ax1.scatter(alpha_positions[:, 1], alpha_positions[:, 2], c='r', s=50)
    for pos in alpha_positions:
        ax1.annotate(f'LED{int(pos[0])}', (pos[1], pos[2]))
    ax1.set_title('Alpha Plan (0°)')

    # Plot beta plan (90 degrees)
    try:
        img_beta = cv2.imread('data/plan_beta.jpg')  # Updated path to include data folder
        if img_beta is not None:
            img_beta = cv2.cvtColor(img_beta, cv2.COLOR_BGR2RGB)
            ax2.imshow(img_beta)
    except:
        ax2.set_facecolor('black')

    ax2.scatter(beta_positions[:, 1], beta_positions[:, 2], c='r', s=50)
    for pos in beta_positions:
        ax2.annotate(f'LED{int(pos[0])}', (pos[1], pos[2]))
    ax2.set_title('Beta Plan (90°)')

    # Store matched LED coordinates
    matched_leds = {}

    # Create 3D visualization
    # For alpha plane (YZ plane at x=0)
    for pos_alpha in alpha_positions:
        led_id_alpha = int(pos_alpha[0])
        # Get coordinates from alpha plan
        y_alpha = (pos_alpha[1] - alpha_positions[0, 1]) / 1920  # Normalize Y coordinate
        x_alpha = 0  # This is the alpha plane at x=0
        
        # Plot point on YZ plane (alpha)
        ax3.scatter(x_alpha, y_alpha, 0, c='r', s=50)
        ax3.text(x_alpha, y_alpha, 0, f'LED{led_id_alpha}')
        
        # Look for matching LED in beta positions
        for pos_beta in beta_positions:
            led_id_beta = int(pos_beta[0])
            if led_id_alpha == led_id_beta:
                # Get coordinates from beta plan
                x_beta = (pos_beta[1] - beta_positions[0, 1]) / 1920  # Normalize X coordinate
                y_beta = (pos_beta[2] - beta_positions[0, 2]) / 1080  # Use Y from beta
                
                # Plot point on XZ plane (beta)
                ax3.scatter(x_beta, 0, 0, c='b', s=50)
                ax3.text(x_beta, 0, 0, f'LED{led_id_beta}')
                
                # Calculate Z coordinate using triangulation from both planes
                z = abs(y_alpha - y_beta)  # Z is the difference between Y coordinates
                
                # Store matched coordinates
                matched_leds[led_id_alpha] = {
                    "id": led_id_alpha,
                    "x": float(x_beta),    # X from beta plane
                    "y": float(y_alpha),   # Y from alpha plane
                    "z": float(z)          # Z calculated from difference
                }
                
                # Plot intersection point
                ax3.scatter(x_beta, y_alpha, z, c='g', s=100)
                ax3.text(x_beta, y_alpha, z, f'LED{led_id_alpha}')

    # Calculate symmetric range for axes
    max_range = max(
        abs(max(matched_leds[led]["x"] for led in matched_leds)),
        abs(min(matched_leds[led]["x"] for led in matched_leds)),
        abs(max(matched_leds[led]["y"] for led in matched_leds)),
        abs(min(matched_leds[led]["y"] for led in matched_leds)),
        abs(max(matched_leds[led]["z"] for led in matched_leds)),
        abs(min(matched_leds[led]["z"] for led in matched_leds))
    )
    max_range = max(max_range, 0.5)  # Ensure minimum range
    
    # Create grid for planes
    xx, zz = np.meshgrid([-max_range, max_range], [-max_range, max_range])
    
    # Alpha plane (YZ at x=0) - RED plane
    ax3.plot_surface(
        np.zeros_like(xx),
        xx,
        zz,
        alpha=0.2, color='red'
    )

    # Beta plane (XZ at y=0) - BLUE plane
    ax3.plot_surface(
        xx,
        np.zeros_like(xx),
        zz,
        alpha=0.2, color='blue'
    )

    # Set equal aspect ratio and symmetric limits
    ax3.set_box_aspect([1, 1, 1])
    ax3.set_xlim([-max_range, max_range])
    ax3.set_ylim([-max_range, max_range])
    ax3.set_zlim([-max_range, max_range])

    # Update axis labels
    ax3.set_xlabel('X')
    ax3.set_ylabel('Y')
    ax3.set_zlabel('Z')
    ax3.set_title('3D View')

    # Add coordinate system visualization
    ax3.plot([-max_range, max_range], [0, 0], [0, 0], 'k--', alpha=0.3)  # X axis
    ax3.plot([0, 0], [-max_range, max_range], [0, 0], 'k--', alpha=0.3)  # Y axis
    ax3.plot([0, 0], [0, 0], [-max_range, max_range], 'k--', alpha=0.3)  # Z axis

    # Add origin point
    ax3.scatter(0, 0, 0, c='k', s=100, marker='*', label='Origin (0,0,0)')
    ax3.legend()

    # Save 3D coordinates to text file in data folder
    with open('data/led_3d_coordinates.txt', 'w') as f:
        f.write("LED ID, X, Y, Z\n")
        for led_data in sorted(matched_leds.items()):
            led = led_data[1]  # Get the dictionary of coordinates
            f.write(f"LED {led['id']}: ({led['x']:.2f}, {led['y']:.2f}, {led['z']:.2f})\n")

    # Add legend entry for intersection points
    ax3.scatter([], [], [], c='g', s=100, label='LED Intersections')
    ax3.plot([], [], 'g--', label='Perpendicular Lines')
    
    # Update legend
    ax3.legend()

    # Adjust layout and display
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()