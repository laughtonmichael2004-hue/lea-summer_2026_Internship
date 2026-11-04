'''
Fill in
'''

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


def plot_data(data_file, trimmed_path_file):

    # Tell NumPy it's comma-separated
    data = np.loadtxt(data_file, delimiter=',', skiprows=1)  # Skip the header row
    print(data)
    try:
        x = data[:, 0]
        y = data[:, 1]
        yerr = data[:, 2]
        plt.errorbar(x, y, yerr=yerr, fmt='-', capsize=3, linestyle='-', marker='o', label=f"{trimmed_path_file}", zorder=1)

    except IndexError:
        # Handles the case when the data has only one row (single data point)
        x = data[0]
        y = data[1]
        yerr = data[2]
        plt.errorbar(x, y, yerr=yerr, fmt='-', capsize=3, marker='o', label=f"{trimmed_path_file}", zorder=1)
    

save_fig = True  # Set to True to save the figure as a PNG file, False to just display it
path = Path(r"C:\Users\laugh\lea-summer-2026-internship-forked\lea-summer_2026_Internship\2. Deuterium Lamp\Spectrum_calibration_data_(03-11-2026)")  # Replace with the actual path to your data files
path_prefix = path
path_suffix = ".txt"

fig, ax = plt.subplots(figsize=(8, 5))

try:
    # Iterates over all .txt files in the specified directory and processes them
    for target in path.glob("*.txt"):
        trimmed_path_file = target.stem
        print(str(target))
        try:

            plot_data(target, trimmed_path_file)

        except:
            print(f"File {target} failed to plot.")        

except:
    print(f"Error occurred while trying to glob files.")

ax.set_xlabel('Wavelength (nm)', fontsize=12)
ax.set_ylabel('Photocurrent (A)', fontsize=12)
ax.set_title('Avg. Photocurrent vs Wavelength (Hole Comparison)', fontsize=14)
ax.set_yscale('log')
ax.grid(True, alpha=0.3)

ax.legend()

plt.tight_layout()

if save_fig:
    plt.savefig(r"C:\Users\laugh\lea-summer-2026-internship-forked\lea-summer_2026_Internship\2. Deuterium Lamp\Figures\(03-11-2026)\peak_intensity_hole_comparison_(03-11-2026).png", dpi=600, bbox_inches='tight')

plt.show()
