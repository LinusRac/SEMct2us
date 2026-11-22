"""Python reference point-scatterer backend with a Field II-style RF interface."""
import numpy as np


class ReferenceScattererBackend:
    name = "reference"

    def simulate(self, positions_m, amplitudes, acquisition, mean_speed_m_s):
        fs = float(acquisition["sampling_frequency_hz"])
        fc = float(acquisition["center_frequency_hz"])
        depth = float(acquisition["depth_mm"]) / 1000.0
        lines = int(acquisition["scan_lines"])
        aperture = int(acquisition["element_count"]) * (
            float(acquisition["element_width_mm"]) + float(acquisition["element_kerf_mm"])
        ) / 1000.0
        wavelength = mean_speed_m_s / fc
        tx_focus = float(acquisition["transmit_focus_mm"]) / 1000.0
        rx_focus = float(acquisition["receive_focus_mm"]) / 1000.0
        samples = int(np.ceil(2 * depth / mean_speed_m_s * fs))
        rf = np.zeros((lines, samples), dtype=np.float32)
        line_x = np.linspace(-float(acquisition["lateral_extent_mm"]) / 2000.0,
                             float(acquisition["lateral_extent_mm"]) / 2000.0, lines)
        pulse_t = np.arange(-3 / fc, 3 / fc, 1 / fs)
        pulse = np.sin(2 * np.pi * fc * pulse_t) * np.exp(-(pulse_t * fc) ** 2 * 3)
        for i, x0 in enumerate(line_x):
            distance = np.hypot(positions_m[:, 0] - x0, positions_m[:, 1])
            beam_width = np.maximum(wavelength * positions_m[:, 1] / max(aperture, 1e-6), 1e-4)
            aperture_weight = np.exp(-0.5 * ((positions_m[:, 0] - x0) / beam_width) ** 2)
            focus_weight = np.exp(-0.5 * ((distance - tx_focus) / max(tx_focus, 1e-3)) ** 2)
            focus_weight *= np.exp(-0.5 * ((distance - rx_focus) / max(rx_focus, 1e-3)) ** 2)
            sample = np.rint(2 * distance / mean_speed_m_s * fs).astype(int)
            valid = (sample > len(pulse) // 2) & (sample < samples - len(pulse) // 2)
            for center, amp, d, weight in zip(
                sample[valid], amplitudes[valid], distance[valid],
                aperture_weight[valid] * focus_weight[valid],
            ):
                left = center - len(pulse) // 2
                rf[i, left:left + len(pulse)] += amp * weight * pulse / max(d, 1e-3)
        return rf
