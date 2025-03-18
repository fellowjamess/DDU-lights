import numpy as np
import matplotlib.pyplot as plt
import cv2

def setup_camera():
    # Placeholder function for setting up the camera
    pass

def main():
    camera = setup_camera()
    
    # Create window for mask visualization
    cv2.namedWindow('Mask View', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Mask View', 640, 480)
    
    # Load the coordinate data
    try:
        alpha_positions = np.load('plan_alpha.npy')
        beta_positions = np.load('plan_beta.npy')
    except FileNotFoundError:
        print("Error: Could not find plan data files. Run plan.py first.")
        return

    # Create figure with two subplots side by side
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))

    # Plot alpha plan (0 degrees)
    try:
        img_alpha = cv2.imread('plan_alpha.jpg')
        if img_alpha is not None:
            # Convert BGR to RGB for matplotlib
            img_alpha = cv2.cvtColor(img_alpha, cv2.COLOR_BGR2RGB)
            ax1.imshow(img_alpha)
    except:
        ax1.set_facecolor('black')

    # Plot LED positions on alpha plan
    ax1.scatter(alpha_positions[:, 1], alpha_positions[:, 2], c='r', s=50)
    # Add LED index labels
    for pos in alpha_positions:
        ax1.annotate(f'LED{int(pos[0])}', (pos[1], pos[2]))
    ax1.set_title('Alpha Plan (0°)')

    # Plot beta plan (90 degrees)
    try:
        img_beta = cv2.imread('plan_beta.jpg')
        if img_beta is not None:
            # Convert BGR to RGB for matplotlib
            img_beta = cv2.cvtColor(img_beta, cv2.COLOR_BGR2RGB)
            ax2.imshow(img_beta)
    except:
        ax2.set_facecolor('black')

    # Plot LED positions on beta plan
    ax2.scatter(beta_positions[:, 1], beta_positions[:, 2], c='r', s=50)
    # Add LED index labels
    for pos in beta_positions:
        ax2.annotate(f'LED{int(pos[0])}', (pos[1], pos[2]))
    ax2.set_title('Beta Plan (90°)')

    # Adjust layout and display
    plt.tight_layout()
    plt.show()

    try:
        pass  # Placeholder for additional code
    finally:
        # Clean up
        cv2.destroyAllWindows()  # Close all OpenCV windows

if __name__ == "__main__":
    main()