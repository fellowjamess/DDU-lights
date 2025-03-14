import numpy as np
import matplotlib.pyplot as plt

# Load the .npy file
data = np.load('led_coordinates.npy', allow_pickle=True)

# Print the data structure
print("Data shape:", data.shape)
print("\nFirst few entries:")
print(data[:5])

# If the data contains 3D coordinates, visualize them
if len(data.shape) >= 2:
    # Extract coordinates
    coordinates = np.array([pos[1] for pos in data])
    
    # Create 3D plot
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot points
    ax.scatter(coordinates[:, 0], coordinates[:, 1], coordinates[:, 2])
    
    # Labels
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('LED Positions in 3D Space')
    
    plt.show()