import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from pathlib import Path

# Get the file

data_file = Path(r"C:\Users\laugh\lea-summer-2026-internship-forked\lea-summer_2026_Internship\2. Deuterium Lamp\Spectrum_calibration_data_(03-11-2026)\Calibration_spectrum\outputted_calib_data\calibration_data_(03-11-2026).txt")
save_fig = False

# Load the data and extract the data

data = np.loadtxt(data_file, delimiter=',', skiprows=1)
x1, x2, y = data[:, 0], data[:, 1], data[:, 2]

#Assume data is sorted by angle (x1) and wavelength (x2). If not, might need to sort it first...
x1s, x2s, ys = x1, x2, y

# Tune the prominence parameter as needed to detect the peaks of interest
peaks, _ = find_peaks(ys, prominence=0.1 * (ys.max() - ys.min()))

peak_angles = x1s[peaks]
peak_wls = x2s[peaks]
peak_currents = ys[peaks]

# Print a table I love table

print(f"| {'Angle (deg)':>12} | {'Wavelength (nm)':>16} | {'Photocurrent (A)':>18} |")
print("|" + "/" * 14 + "|" + "/" * 18 + "|" + "/" * 20 + "|")
for ang, w, c in zip(peak_angles, peak_wls, peak_currents):
    print(f"| {ang:12.3f} | {w:16.2f} | {c:18.3e} |")

# Plotting

fig, ax = plt.subplots(figsize=(8, 5), layout='constrained')

ax.plot(x1, y, linestyle='-', marker='o', zorder=1)

ax.set_xlabel(r'Angle ($\theta$ in degrees)', fontsize=12)
ax.set_ylabel('Photocurrent (A)', fontsize=12)
ax.set_ylim(-5, 105)
ax.set_title('Deuterium Lamp Calibration Spectrum', fontsize=14, pad=20)
ax.grid(True, alpha=0.3)

# Mark and label peaks on the plot
ax.plot(peak_angles, peak_currents, 'rx', markersize=10, zorder=3, label='Peaks')
for ang, w, c in zip(peak_angles, peak_wls, peak_currents):
    ax.annotate(f'{w:.1f} nm', xy=(ang, c), xytext=(-10, -10),
                textcoords='offset points', ha='right', fontsize=9)
    ax.vlines(ang, ymin=-5, ymax=105, color='red', linestyle='--', zorder=2)
    
ax.legend()

# Define the secondary x-axis for wavelength

# Angle to wavelength mapping from the calibration data, assumed a linear fitting for the interpolation since I just want to plot the values I have.
# Makes sense they have some cosntant offset... perhaps should have used the function seen in the wavelength conversion...
a, b = np.polyfit(x1, x2, 1)          

angle_to_wl = lambda theta: a * theta + b
wl_to_angle = lambda wl: (wl - b) / a

secax = ax.secondary_xaxis('top', functions=(angle_to_wl, wl_to_angle))
secax.set_xlabel('Wavelength (nm)', fontsize=12, labelpad=10)

if save_fig:
    fig.savefig("calibration_spectrum_angle_wavelength_(02-11-2026).png", dpi=600, bbox_inches='tight')

plt.show()