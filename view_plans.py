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
        y = pos[1]
        z = pos[2]
        ax3.scatter(0, y, z, c='r', s=50)
        ax3.text(0, y, z, f'LED{led_id}')

    # For beta plane (XZ plane at y=0)
    for pos in beta_positions:
        led_id = int(pos[0])
        x = pos[1]  # Using the x coordinate from beta view
        z = pos[2]
        ax3.scatter(x, 0, z, c='b', s=50)
        ax3.text(x, 0, z, f'LED{led_id}')

    # Customize 3D plot
    ax3.set_xlabel('X')
    ax3.set_ylabel('Y')
    ax3.set_zlabel('Z')
    ax3.set_title('3D View')

    # Add semi-transparent planes to show the measurement planes
    max_range = max(
        np.max(np.abs(alpha_positions[:, 1:3])),
        np.max(np.abs(beta_positions[:, 1:3]))
    )
    xx, zz = np.meshgrid([-max_range, max_range], [-max_range, max_range])
    yy = np.zeros_like(xx)

    # Alpha plane (YZ at x=0)
    ax3.plot_surface(
        np.zeros_like(xx), xx, zz,
        alpha=0.2, color='red'
    )

    # Beta plane (XZ at y=0)
    ax3.plot_surface(
        xx, np.zeros_like(xx), zz,
        alpha=0.2, color='blue'
    )

    # Set equal aspect ratio for 3D plot
    ax3.set_box_aspect([1, 1, 1])

    # Adjust layout and display
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()