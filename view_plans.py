import numpy as np
import matplotlib.pyplot as plt
import cv2
from mpl_toolkits.mplot3d import Axes3D

def main():
    # Load the coordinate data
    try:
        alpha_positions = np.load('plan_alpha.npy')
        beta_positions = np.load('plan_beta.npy')
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
        img_alpha = cv2.imread('plan_alpha.jpg')
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
        img_beta = cv2.imread('plan_beta.jpg')
        if img_beta is not None:
            img_beta = cv2.cvtColor(img_beta, cv2.COLOR_BGR2RGB)
            ax2.imshow(img_beta)
    except:
        ax2.set_facecolor('black')

    ax2.scatter(beta_positions[:, 1], beta_positions[:, 2], c='r', s=50)
    for pos in beta_positions:
        ax2.annotate(f'LED{int(pos[0])}', (pos[1], pos[2]))
    ax2.set_title('Beta Plan (90°)')

    # Create 3D visualization
    # For alpha plane (YZ plane at x=0)
    for pos in alpha_positions:
        led_id = int(pos[0])
        # Shift coordinates to start from origin (0,0,0) and ensure they're positive
        y = abs(pos[1] - alpha_positions[0, 1])  # Make y position positive
        z = abs(pos[2] - alpha_positions[0, 2])  # Make z position positive
        ax3.scatter(0, y, z, c='r', s=50)
        ax3.text(0, y, z, f'LED{led_id}')

    # For beta plane (XZ plane at y=0) - Perpendicular to alpha plane
    for pos in beta_positions:
        led_id = int(pos[0])
        # Shift coordinates to start from origin (0,0,0) and ensure they're positive
        x = abs(pos[1] - beta_positions[0, 1])   # Make x position positive
        z = abs(pos[2] - beta_positions[0, 2])   # Make z position positive
        ax3.scatter(x, 0, z, c='b', s=50)
        ax3.text(x, 0, z, f'LED{led_id}')

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

    # Adjust layout and display
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()