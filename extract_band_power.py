"""
Extract band power features from the s52.mat EEG dataset.
Mirrors the band power output that Emotiv Cortex provides (theta, alpha, betaL, betaH, gamma).
"""

import os
import scipy.io
import numpy as np
from scipy.signal import welch

# ---- Define frequency bands (same as Emotiv) ----
BANDS = {
    'theta':  (4, 8),
    'alpha':  (8, 12),
    'betaL':  (12, 16),   # Emotiv "low beta"
    'betaH':  (16, 25),   # Emotiv "high beta"
    'gamma':  (25, 45),
}


def compute_band_power(eeg_data, srate, window_sec=2.0):
    """
    Compute band power for each channel using Welch's method.

    Parameters
    ----------
    eeg_data : ndarray, shape (n_channels, n_samples)
        Raw EEG data
    srate : int
        Sampling rate in Hz
    window_sec : float
        Window length for Welch PSD estimation

    Returns
    -------
    band_powers : dict
        {band_name: array of shape (n_channels,)} with power in each band
    freqs : ndarray
        Frequency axis from Welch
    psd : ndarray
        Full PSD, shape (n_channels, n_freqs)
    """
    nperseg = int(window_sec * srate)  # samples per segment

    # Welch PSD for all channels
    freqs, psd = welch(eeg_data, fs=srate, nperseg=nperseg, axis=1)

    # Extract power in each band
    band_powers = {}
    for band_name, (f_low, f_high) in BANDS.items():
        idx = np.where((freqs >= f_low) & (freqs <= f_high))[0]
        band_powers[band_name] = np.mean(psd[:, idx], axis=1)

    return band_powers, freqs, psd


def run_analysis(mat_path=None):
    """
    Run full band power extraction. Returns a dict suitable for JSON (no numpy types).
    If mat_path is None, tries: env S52_MAT_PATH, then ./s52.mat, then c:\\Users\\User\\Downloads\\s52.mat
    """
    if mat_path is None:
        mat_path = os.environ.get('S52_MAT_PATH')
    if mat_path is None:
        mat_path = os.path.join(os.path.dirname(__file__), 's52.mat')
    if not os.path.isfile(mat_path):
        fallback = r'c:\Users\User\Downloads\s52.mat'
        if os.path.isfile(fallback):
            mat_path = fallback
        else:
            return {'error': f'MAT file not found. Tried: {mat_path} and {fallback}'}

    mat = scipy.io.loadmat(mat_path)
    eeg = mat['eeg'][0, 0]

    srate = int(eeg['srate'][0, 0])
    n_channels = 68

    # Resting state
    rest_data = eeg['rest']
    rest_powers, freqs, rest_psd = compute_band_power(rest_data, srate)

    # Single imagery trial (trial 1)
    imagery_left = eeg['imagery_left']
    frame = eeg['frame'].flatten()
    n_trials = int(eeg['n_imagery_trials'][0, 0])
    trial_samples = int((frame[1] - frame[0]) / 1000 * srate)
    pre_samples = int(abs(frame[0]) / 1000 * srate)

    trial_idx = 0
    trial_start = trial_idx * trial_samples
    trial_end = trial_start + trial_samples
    trial_data = imagery_left[:, trial_start:trial_end]
    trial_powers, _, _ = compute_band_power(trial_data, srate)

    # Emotiv-style mapping
    emotiv_map = {'AF3': 0, 'T7': 10, 'Pz': 31, 'T8': 40, 'AF4': 3}
    emotiv_pow_vector = []
    emotiv_trial = {}
    for elec, ch_idx in emotiv_map.items():
        emotiv_trial[elec] = {}
        for band in BANDS:
            val = float(trial_powers[band][ch_idx])
            emotiv_trial[elec][band] = round(val, 3)
            emotiv_pow_vector.append(round(val, 3))

    # Time-series alpha (2s window, 0.5s step)
    window_samples = 2 * srate
    step_samples = srate // 2
    n_windows = (trial_data.shape[1] - window_samples) // step_samples + 1
    alpha_over_time = []
    for w in range(n_windows):
        start = w * step_samples
        end = start + window_samples
        segment = trial_data[:, start:end]
        seg_powers, _, _ = compute_band_power(segment, srate, window_sec=1.0)
        t = (start - pre_samples) / srate
        row = {'time_s': round(t, 1)}
        for elec, ch_idx in emotiv_map.items():
            row[elec] = round(float(seg_powers['alpha'][ch_idx]), 1)
        alpha_over_time.append(row)

    # Convert rest/trial tables to list of dicts for JSON (first 5 channels)
    def band_table(powers, n_ch=5):
        rows = []
        for ch in range(n_ch):
            row = {'channel': ch}
            for band in BANDS:
                row[band] = round(float(powers[band][ch]), 1)
            rows.append(row)
        return rows

    return {
        'srate': srate,
        'n_channels': n_channels,
        'bands': list(BANDS.keys()),
        'band_hz': {k: list(v) for k, v in BANDS.items()},
        'rest_shape': list(rest_data.shape),
        'rest_band_power': band_table(rest_powers),
        'trial_shape': list(trial_data.shape),
        'trial_band_power': band_table(trial_powers),
        'emotiv_trial': emotiv_trial,
        'emotiv_pow_vector': emotiv_pow_vector,
        'alpha_over_time': alpha_over_time,
    }


if __name__ == '__main__':
    # CLI: run and print
    print("Loading MAT file...")
    result = run_analysis()
    if 'error' in result:
        print(result['error'])
        exit(1)
    print(f"Sampling rate: {result['srate']} Hz")
    print(f"Channels: {result['n_channels']}")
    print("\nRest band power (first 5 channels):", result['rest_band_power'])
    print("\nTrial band power (first 5 channels):", result['trial_band_power'])
    print("\nEmotiv-style:", result['emotiv_trial'])
    print("\nDone!")
