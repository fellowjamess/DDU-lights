import numpy as np
import os

# NUMMER_OF_LEDS = 40

def create_data():
    if not os.path.exists('data'):
        os.makedirs('data')

    # Front view (alpha)
    alpha_positions = []

    # Tree
    levels = 5
    leds_per_level = [4, 6, 8, 10, 12] # From top to bottom, total 40 LEDs
    tree_height = 800 # Total height in pixels
    base_width = 800 # Width at bottom in pixels

    led_id = 0
    for row in range(levels):
        num_leds = leds_per_level[row]
        level_width = base_width * (1 - (row/levels) * 0.8)
        start_x = 960 - (level_width // 2)
        spacing = level_width / (num_leds - 1) if num_leds > 1 else 0

        y = 200 + (row * (tree_height / (levels - 1)))

        for col in range(num_leds):
            x = start_x + col * spacing
            alpha_positions.append((led_id, x, y))
            led_id += 1

    # Side view (beta)
    beta_positions = []
    led_id = 0

    for row in range(levels):
        num_leds = leds_per_level[row]

        row_depth = 400 * (1 - (row/levels) * 0.6)
        y = 200 + (row * (tree_height / (levels - 1)))

        for col in range(num_leds):
            angle = (col / (num_leds - 1)) * np.pi
            depth = 960 + row_depth * np.cos(angle)
            beta_positions.append((led_id, depth, y))
            led_id += 1

    # Save the data
    np.save('data/plan_alpha.npy', np.array(alpha_positions))
    np.save('data/plan_beta.npy', np.array(beta_positions))

    print("Fake christmas tree data created:")
    print(f"Alpha positions: {len(alpha_positions)} LEDs")
    print(f"Beta positions: {len(beta_positions)} LEDs")

if __name__ == "__main__":
    create_data()