import numpy as np
import matplotlib.pyplot as plt
import cv2
import os

def create_coordinate_system(positions, image, angle_name):
    # Create figure for 2D visualization
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111)

    # Display the original image
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    ax.imshow(img_rgb, alpha=0.5)

    # Plot LED positions
    for pos in positions:
        led_id = int(pos[0])
        x = pos[1]
        y = pos[2]
        
        # Convert to centered coordinates
        x_centered = x - image.shape[1]//2
        y_centered = -(y - image.shape[0]//2)  # Invert Y to match standard coordinates
        
        # Plot point
        ax.scatter(x, y, c='r', s=50)
        # Add label with centered coordinates
        ax.annotate(f'LED{led_id}\n({x_centered:.0f}, {y_centered:.0f})', 
                   (x, y),
                   xytext=(0, 10),
                   textcoords='offset points',
                   ha='center',
                   bbox=dict(facecolor='white', alpha=0.7))

    # Draw coordinate axes
    ax.axhline(y=image.shape[0]//2, color='b', linestyle='--', alpha=0.5)
    ax.axvline(x=image.shape[1]//2, color='b', linestyle='--', alpha=0.5)

    # Set labels and title
    ax.set_xlabel('Camera X (pixels)')
    ax.set_ylabel('Camera Y (pixels)')
    ax.set_title(f'{angle_name} Plan LED Positions\nCoordinates Centered on Camera')

    # Save visualization
    plt.savefig(f'data/coordinates/xy_coordinate_system_{angle_name.lower()}.png', 
                dpi=300, 
                bbox_inches='tight',
                facecolor='white')

    # Save centered coordinates to text file
    with open(f'data/coordinates/led_xy_coordinates_{angle_name.lower()}.txt', 'w') as f:
        f.write(f"LED ID, X, Y (origin at camera center) - {angle_name} Plan\n")
        for pos in positions:
            led_id = int(pos[0])
            x_centered = pos[1] - image.shape[1]//2
            y_centered = -(pos[2] - image.shape[0]//2)
            f.write(f"LED {led_id}: ({x_centered:.0f}, {y_centered:.0f})\n")

    plt.close()

def main():
    # Load both sets of data
    try:
        # Load alpha plan data
        alpha_positions = np.load('data/plan_alpha.npy')
        img_alpha = cv2.imread('data/plan_alpha.jpg')
        if img_alpha is None:
            raise FileNotFoundError("Could not load alpha plan image")
            
        # Load beta plan data
        beta_positions = np.load('data/plan_beta.npy')
        img_beta = cv2.imread('data/plan_beta.jpg')
        if img_beta is None:
            raise FileNotFoundError("Could not load beta plan image")
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure to run plan.py first to generate the data.")
        return

    # Ensure coordinates folder exists
    os.makedirs('data/coordinates', exist_ok=True)

    # Create coordinate systems for both plans
    create_coordinate_system(alpha_positions, img_alpha, "Alpha")
    create_coordinate_system(beta_positions, img_beta, "Beta")

    print(f"Data saved in data/coordinates/:")
    print("- xy_coordinate_system_alpha.png (Alpha plan visualization)")
    print("- xy_coordinate_system_beta.png (Beta plan visualization)")
    print("- led_xy_coordinates_alpha.txt (Alpha plan coordinate data)")
    print("- led_xy_coordinates_beta.txt (Beta plan coordinate data)")

    # Display both plots
    plt.figure(figsize=(15, 6))
    
    # Alpha plan
    plt.subplot(121)
    img_alpha_rgb = cv2.cvtColor(img_alpha, cv2.COLOR_BGR2RGB)
    plt.imshow(img_alpha_rgb, alpha=0.5)
    plt.title("Alpha Plan (0°)")
    
    # Beta plan
    plt.subplot(122)
    img_beta_rgb = cv2.cvtColor(img_beta, cv2.COLOR_BGR2RGB)
    plt.imshow(img_beta_rgb, alpha=0.5)
    plt.title("Beta Plan (90°)")
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()