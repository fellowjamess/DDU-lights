import numpy as np
import matplotlib.pyplot as plt

# Load the coordinates from the position folder
data = np.load('position/led_coordinates.npz')
indices = data['indices']
positions = data['positions']

# Center coordinates around camera (make camera the origin)
positions = np.array(positions)
center = np.mean(positions, axis=0)  # Find center of all points
positions = positions - center  # Translate all points

# Print summary with camera-centered coordinates
print(f"Found {len(indices)} valid LED positions (relative to camera)")
for i, pos in zip(indices, positions):
    print(f"LED {i}: Position {pos}")

# Create 3D plot
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Plot points
ax.scatter(positions[:, 0], positions[:, 1], positions[:, 2], c='r', s=50)

# Add LED indices as labels
for i, pos in zip(indices, positions):
    ax.text(pos[0], pos[1], pos[2], f'LED{i}')

# Plot camera position (origin)
ax.scatter(0, 0, 0, c='b', s=100, marker='*', label='Camera (Origin)')

# Add coordinate axes
max_range = np.max(np.abs(positions))
ax.plot([-max_range, max_range], [0, 0], [0, 0], 'k--', alpha=0.3)  # X axis
ax.plot([0, 0], [-max_range, max_range], [0, 0], 'k--', alpha=0.3)  # Y axis
ax.plot([0, 0], [0, 0], [-max_range, max_range], 'k--', alpha=0.3)  # Z axis

# Set equal aspect ratio
ax.set_box_aspect([1, 1, 1])

# Set axis labels and title
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('LED Positions Relative to Camera')

# Add legend
ax.legend()

plt.show()