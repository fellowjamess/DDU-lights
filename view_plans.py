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
        # Normalize coordinates relative to first LED
        y = (pos_alpha[1] - alpha_positions[0, 1]) / 1920
        z = (pos_alpha[2] - alpha_positions[0, 2]) / 1080
        
        # Plot point on YZ plane (alpha)
        ax3.scatter(0, y, z, c='r', s=50)
        ax3.text(0, y, z, f'LED{led_id_alpha}')
        
        # Look for matching LED in beta positions
        for pos_beta in beta_positions:
            led_id_beta = int(pos_beta[0])
            if led_id_alpha == led_id_beta:
                # Convert beta coordinates (now on XZ plane)
                x = (pos_beta[1] - beta_positions[0, 1]) / 1920
                z_beta = (pos_beta[2] - beta_positions[0, 2]) / 1080
                
                # Plot point on XZ plane (beta)
                ax3.scatter(x, 0, z_beta, c='b', s=50)
                ax3.text(x, 0, z_beta, f'LED{led_id_beta}')
                
                # Store matched coordinates
                matched_leds[led_id_alpha] = {
                    "id": led_id_alpha,
                    "x": float(x),
                    "y": float(y),
                    "z": float((z + z_beta) / 2)  # Average Z coordinates
                }
                
                # Plot intersection point in green
                ax3.scatter(x, y, (z + z_beta) / 2, c='g', s=100)
                ax3.text(x, y, (z + z_beta) / 2, f'LED{led_id_alpha}')

    # Customize 3D plot
    ax3.set_xlabel('X')
    ax3.set_ylabel('Y')
    ax3.set_zlabel('Z')
    ax3.set_title('3D View')

    # Calculate positive max range
    max_range = max(
        np.max([abs(pos[1] - alpha_positions[0, 1]) for pos in alpha_positions]),
        np.max([abs(pos[1] - beta_positions[0, 1]) for pos in beta_positions]),
        np.max([abs(pos[2] - alpha_positions[0, 2]) for pos in alpha_positions]),
        np.max([abs(pos[2] - beta_positions[0, 2]) for pos in beta_positions])
    )
    
    # Create grid for planes (only positive values)
    xx, zz = np.meshgrid([0, max_range], [0, max_range])
    
    # Alpha plane (YZ at x=0) - RED plane
    ax3.plot_surface(
        np.zeros_like(xx),  # x = 0 plane
        xx,                 # y values (positive only)
        zz,                # z values (positive only)
        alpha=0.2, color='red'
    )

    # Beta plane (XZ at y=0) - BLUE plane
    ax3.plot_surface(
        xx,                # x values (positive only)
        np.zeros_like(xx), # y = 0 plane
        zz,                # z values (positive only)
        alpha=0.2, color='blue'
    )

    # Set equal aspect ratio for 3D plot
    ax3.set_box_aspect([1, 1, 1])

    # Set the viewing angle to better show perpendicular planes
    ax3.view_init(elev=20, azim=45)

    # Adjust plot limits to show only positive values
    ax3.set_xlim([0, max_range])
    ax3.set_ylim([0, max_range])
    ax3.set_zlim([0, max_range])

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