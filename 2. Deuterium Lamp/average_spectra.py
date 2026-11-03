"""
Average spectrum data files and save the result as a new .txt file.

What the program does, in order:
  1. Loads a single spectrum file, or every .txt file in a directory, and
     averages the photocurrents (combining the errors).
  2. Converts the actuator angles to wavelengths using the calibration
     parameters (gamma, theta0) obtained from calibrate_A.py.
  3. Saves a new CSV-formatted .txt file with the columns:
         wavelength_nm, photocurrent_avg_A, photocurrent_std_A
     ready to be plotted elsewhere.

Expected input file columns:
    angle_deg, epos, current_mean_A, current_std_A, n_samples

Usage examples:
    python average_spectra.py "path/to/spectrum_folder"
    python average_spectra.py "path/to/spectrum_folder" --calib_params 0.9936 1.01126
    python average_spectra.py "path/to/spectrum_folder" --save "path/to/averaged.txt"
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

# Path used when none is given on the command line (a file or a folder). Edit this.
DEFAULT_DATA_DIR = r"C:\Users\laugh\lea-summer-2026-internship-forked\lea-summer_2026_Internship\2. Deuterium Lamp\Spectrum_calibration_data_(30-10-2026)_1"

# Default calibration parameters (gamma, theta0 in degrees), taken from calibrate_A.py.
# Override on the command line with --calib_params GAMMA THETA0.
DEFAULT_CALIB_PARAMS = [0.99360, 1.01126]

# Physical constants for the wavelength conversion (Eq. 20 of Max's report).
D = 835.5    # nm (1 / 1200 lines/mm)
PHI = 35     # degrees (half deviation angle)
M = 1        # first diffraction order


# ---------------------------------------------------------------------------
# ANGLE to WAVELENGTH
# ---------------------------------------------------------------------------

def actuator_angle_to_wavelength(theta_deg, gamma, theta0):
    """
    Convert actuator angle (deg) to wavelength (nm).
    Equation 20 of Max's report: m * lambda = 2 * d * cos(phi) * sin(gamma * (theta - theta0))
    """
    C = 2 * D * np.cos(np.radians(PHI))  # ~1365 nm
    return (C * np.sin(gamma * (np.radians(theta_deg) - np.radians(theta0)))) / M


# ---------------------------------------------------------------------------
# STEP 1: LOAD AND AVERAGE
# ---------------------------------------------------------------------------

def load_single_file(file_path: Path):
    """
    Load a single .txt file and return the angle, photocurrent, and std arrays.
    Raises an exception if the file cannot be read or lacks required columns.
    """
    df = pd.read_csv(file_path)
    # Assumed format: angle_deg, epos, current_mean_A, current_std_A, n_samples
    angle = df["angle_deg"].to_numpy()
    photocurrent = df["current_mean_A"].to_numpy()
    # Standard error of the mean for this file
    photocurrent_std = (df["current_std_A"] / np.sqrt(df["n_samples"])).to_numpy()
    return angle, photocurrent, photocurrent_std


def load_and_average(path: Path):
    """
    Load spectrum data from `path`, which can be either:
      - a single file: its data is returned as-is, or
      - a directory: every .txt file in it is read and averaged together.

    Returns (angle, photocurrent_avg, photocurrent_std) as numpy arrays.
    For a directory, the per-file errors (std / sqrt(n_samples)) are combined
    as variances and the std of the average is sqrt(total_variance / num_files).
    For a single file, the std returned is that file's standard error.
    """
    # --- Single file case: nothing to average ---
    if path.is_file():
        print(f"Processing single file: {path}")
        return load_single_file(path)

    # --- Directory case: average all .txt files ---
    elif path.is_dir():
        total_sum_photocurrent = None   # running sum of photocurrent over files
        total_sum_variance = None       # running sum of variances over files
        reference_angle = None          # angle array of the first good file
        num_files = 0                   # how many files were processed successfully

        for target in sorted(path.glob("*.txt")):
            print(target)

            # Try to read the file; skip it if it cannot be read or lacks columns
            try:
                angle, photocurrent, photocurrent_std = load_single_file(target)
            except Exception as e:
                print(f"  Skipping {target.name}: failed to load/process ({e})")
                continue

            if total_sum_photocurrent is None:
                # First good file: start the running sums
                total_sum_photocurrent = photocurrent.copy()
                total_sum_variance = photocurrent_std ** 2
                reference_angle = angle
            else:
                # The files are assumed to share the same angle range. Warn if not,
                # since adding arrays of different angles would be wrong.
                if len(angle) != len(reference_angle):
                    print(f"  Skipping {target.name}: different number of points.")
                    continue
                if not np.array_equal(reference_angle, angle):
                    print(f"  Warning: angle values in {target.name} differ from the first file.")
                total_sum_photocurrent += photocurrent
                # Combine variances so the std of the average can be found later
                total_sum_variance += photocurrent_std ** 2

            num_files += 1

        if num_files == 0:
            raise ValueError(f"No usable .txt files found in directory: {path}")

        photocurrent_avg = total_sum_photocurrent / num_files
        photocurrent_std = np.sqrt(total_sum_variance / num_files)
        print(f"Averaged {num_files} file(s).")
        return reference_angle, photocurrent_avg, photocurrent_std

    else:
        raise ValueError(f"Path is neither a file nor a directory: {path}")


# ---------------------------------------------------------------------------
# STEP 3: SAVE
# ---------------------------------------------------------------------------

def default_save_path(data_path: Path) -> Path:
    """
    Where to save if --save is not given. The output is placed NEXT TO the
    input (not inside the folder), so re-running the script never picks up
    its own output as an input file.
    """
    if data_path.is_dir():
        return data_path.parent / f"{data_path.name}_averaged.txt"
    return data_path.with_name(f"{data_path.stem}_averaged.txt")


def save_spectrum(save_path: Path, wavelength, photocurrent_avg, photocurrent_std):
    """Write the averaged spectrum as a CSV-formatted .txt file."""
    out_df = pd.DataFrame({
        "wavelength_nm": wavelength,
        "photocurrent_avg_A": photocurrent_avg,
        "photocurrent_std_A": photocurrent_std,
    })
    save_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(save_path, index=False)
    print(f"Saved {len(out_df)} rows to {save_path}")


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Average spectrum files, convert angle to wavelength, and save a new .txt file.")
    parser.add_argument("data_path", nargs="*", default=None,
                        help="A single spectrum .txt file, or a directory of .txt files "
                             "to average (optional: falls back to DEFAULT_DATA_DIR)")
    parser.add_argument("--calib_params", nargs=2, type=float, default=DEFAULT_CALIB_PARAMS,
                        metavar=("GAMMA", "THETA0"),
                        help="Calibration parameters (gamma, theta0 in degrees) found using "
                             "calibrate_A.py (default: %(default)s)")
    parser.add_argument("--save", type=Path, default=None,
                        help="Where to save the averaged .txt file "
                             "(default: next to the input, named <name>_averaged.txt)")
    args = parser.parse_args()

    # Build the path. Joining the pieces handles unquoted paths with spaces,
    # and stripping quotes handles the Windows trailing-backslash issue
    # ("C:\\folder\\" arrives with a stray quote on the end).
    if args.data_path:
        raw = " ".join(args.data_path).strip().strip('"').strip("'")
        data_path = Path(raw)
    else:
        data_path = Path(DEFAULT_DATA_DIR)

    # Accept either a file or a folder (load_and_average handles both cases)
    if not data_path.exists():
        parser.error(f"Path not found: {data_path!r}  (check the path and quotes)")

    # 1. Load the data and average
    angle, photocurrent_avg, photocurrent_std = load_and_average(data_path)

    # 2. Convert actuator angles to wavelengths using the calibration parameters
    gamma, theta0 = args.calib_params
    print(f"Using calibration parameters: gamma = {gamma:.5f}, theta0 = {theta0:.5f} deg")
    wavelength = actuator_angle_to_wavelength(angle, gamma, theta0)

    # 3. Save the averaged spectrum
    save_path = args.save if args.save else default_save_path(data_path)
    save_spectrum(save_path, wavelength, photocurrent_avg, photocurrent_std)


if __name__ == "__main__":
    main()