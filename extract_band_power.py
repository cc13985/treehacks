"""
Extract band power features from the s52.mat EEG dataset.
Mirrors the band power output that Emotiv Cortex provides (theta, alpha, betaL, betaH, gamma).
"""

import scipy.io
import numpy as np
from scipy.signal import welch

# ---- Load data ----
print("Loading s52.mat...")
mat = scipy.io.loadmat(r'c:\Users\User\Downloads\s52.mat')
eeg = mat['eeg'][0, 0]

srate = int(eeg['srate'][0, 0])  # 512 Hz
n_channels = 68

print(f"Sampling rate: {srate} Hz")
print(f"Channels: {n_channels}")

# ---- Define frequency bands (same as Emotiv) ----
BANDS = {
    'theta':  (4, 8),
    'alpha':  (8, 12),
    'betaL':  (12, 16),   # Emotiv "low beta"
    'betaH':  (16, 25),   # Emotiv "high beta"
    'gamma':  (25, 45),
}

print(f"\nBand definitions (matching Emotiv):")
for name, (lo, hi) in BANDS.items():
    print(f"  {name}: {lo}-{hi} Hz")


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
        # Find frequency indices within this band
        idx = np.where((freqs >= f_low) & (freqs <= f_high))[0]
        # Mean power in the band for each channel
        band_powers[band_name] = np.mean(psd[:, idx], axis=1)
    
    return band_powers, freqs, psd


# ---- Extract from resting state (baseline) ----
print("\n" + "="*60)
print("RESTING STATE - Band Power")
print("="*60)

rest_data = eeg['rest']  # shape (68, 34048)
print(f"Rest data shape: {rest_data.shape} ({rest_data.shape[1]/srate:.1f} seconds)")

rest_powers, freqs, rest_psd = compute_band_power(rest_data, srate)

print(f"\nBand power per channel (first 5 channels):")
print(f"{'Channel':<10}", end="")
for band in BANDS:
    print(f"{band:>12}", end="")
print()
print("-" * 70)

for ch in range(5):
    print(f"Ch {ch:<7}", end="")
    for band in BANDS:
        print(f"{rest_powers[band][ch]:>12.1f}", end="")
    print()


# ---- Extract from a single imagery trial ----
print("\n" + "="*60)
print("SINGLE IMAGERY TRIAL (left hand, trial #1) - Band Power")
print("="*60)

imagery_left = eeg['imagery_left']    # shape (68, 358400)
frame = eeg['frame'].flatten()        # [-2000, 5000] ms
n_trials = int(eeg['n_imagery_trials'][0, 0])

# Data is pre-epoched: 100 trials x 3584 samples concatenated
trial_samples = int((frame[1] - frame[0]) / 1000 * srate)
pre_samples = int(abs(frame[0]) / 1000 * srate)  # 1024 samples (2s before onset)
print(f"Trial length: {trial_samples} samples ({trial_samples/srate:.1f}s, from {frame[0]}ms to {frame[1]}ms)")
print(f"Trials: {n_trials}, Total samples: {n_trials} x {trial_samples} = {n_trials * trial_samples}")
print(f"Event onset within each trial: sample {pre_samples} (t=0)")

# Extract trial 1 (first 3584 samples)
trial_idx = 0
trial_start = trial_idx * trial_samples
trial_end = trial_start + trial_samples
trial_data = imagery_left[:, trial_start:trial_end]

print(f"Trial 1: samples [{trial_start}:{trial_end}]")
print(f"Trial data shape: {trial_data.shape}")

trial_powers, _, _ = compute_band_power(trial_data, srate)

print(f"\nBand power for trial 1 (first 5 channels):")
print(f"{'Channel':<10}", end="")
for band in BANDS:
    print(f"{band:>12}", end="")
print()
print("-" * 70)

for ch in range(5):
    print(f"Ch {ch:<7}", end="")
    for band in BANDS:
        print(f"{trial_powers[band][ch]:>12.1f}", end="")
    print()


# ---- Compare: How Emotiv would output this ----
print("\n" + "="*60)
print("EMOTIV-STYLE OUTPUT (simulated)")
print("="*60)
print("""
Emotiv Cortex streams 'pow' data like this per sample:
  [AF3/theta, AF3/alpha, AF3/betaL, AF3/betaH, AF3/gamma,
   T7/theta,  T7/alpha,  T7/betaL,  T7/betaH,  T7/gamma,
   Pz/theta,  Pz/alpha,  Pz/betaL,  Pz/betaH,  Pz/gamma,
   T8/theta,  T8/alpha,  T8/betaL,  T8/betaH,  T8/gamma,
   AF4/theta, AF4/alpha, AF4/betaL, AF4/betaH, AF4/gamma]

The .mat file has 68 channels. Mapping approximate equivalents:
  AF3 ~ Ch 0,  T7 ~ Ch 10,  Pz ~ Ch 31,  T8 ~ Ch 40,  AF4 ~ Ch 3
""")

# Approximate channel mapping (68-ch montage to Emotiv Insight positions)
emotiv_map = {
    'AF3': 0,
    'T7':  10,
    'Pz':  31,
    'T8':  40,
    'AF4': 3,
}

print("Simulated Emotiv pow output from trial 1:")
print(f"{'Electrode':<10}", end="")
for band in BANDS:
    print(f"{band:>10}", end="")
print()
print("-" * 60)

emotiv_pow_vector = []
for elec, ch_idx in emotiv_map.items():
    print(f"{elec:<10}", end="")
    for band in BANDS:
        val = trial_powers[band][ch_idx]
        emotiv_pow_vector.append(round(val, 3))
        print(f"{val:>10.3f}", end="")
    print()

print(f"\nAs a flat array (like Emotiv streams it):")
print(f"  {emotiv_pow_vector}")


# ---- Sliding window: band power over time (like real-time Emotiv) ----
print("\n" + "="*60)
print("TIME-SERIES BAND POWER (2s sliding windows, like Emotiv real-time)")
print("="*60)

window_samples = 2 * srate   # 2 second window
step_samples = srate // 2     # 0.5s step (2 Hz update, similar to Emotiv)
n_windows = (trial_data.shape[1] - window_samples) // step_samples + 1

print(f"Window: 2s ({window_samples} samples), Step: 0.5s, Windows: {n_windows}")
print(f"\nAlpha power over time for mapped Emotiv channels:")
print(f"{'Time (s)':<10}", end="")
for elec in emotiv_map:
    print(f"{elec:>10}", end="")
print()
print("-" * 60)

for w in range(n_windows):
    start = w * step_samples
    end = start + window_samples
    segment = trial_data[:, start:end]
    
    seg_powers, _, _ = compute_band_power(segment, srate, window_sec=1.0)
    t = (start - pre_samples) / srate  # time relative to event onset
    print(f"{t:<10.1f}", end="")
    for elec, ch_idx in emotiv_map.items():
        print(f"{seg_powers['alpha'][ch_idx]:>10.1f}", end="")
    print()

print("\nDone!")
