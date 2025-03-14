import numpy as np
import matplotlib.pyplot as plt

# Load the coordinates
data = np.load('led_coordinates.npz')
indices = data['indices']
positions = data['positions']

# Print summary
print(f"Found {len(indices)} valid LED positions")
for i, pos in zip(indices, positions):
    print(f"LED {i}: Position {pos}")

# Create 3D plot
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Plot points
ax.scatter(positions[:, 0], positions[:, 1], positions[:, 2])

# Add LED indices as labels
for i, pos in zip(indices, positions):
    ax.text(pos[0], pos[1], pos[2], f'LED{i}')

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('LED Positions in 3D Space')

plt.show()