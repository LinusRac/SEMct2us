import numpy as np


def make_scatterers(properties: dict[str, np.ndarray], lateral_mm: float, depth_mm: float,
                    max_scatterers: int, seed: int):
    rng = np.random.default_rng(seed)
    scatter = properties["diffuse_scatter"]
    boundary = properties["boundary"].astype(bool)
    active = (scatter > 0) & (properties["speed_m_s"] > 1000)
    yy, xx = np.nonzero(active)
    x = (xx / max(scatter.shape[1] - 1, 1) - 0.5) * lateral_mm / 1000.0
    z = (yy / max(scatter.shape[0] - 1, 1)) * depth_mm / 1000.0
    diffuse = rng.normal(0, scatter[yy, xx]).astype(np.float32)
    by, bx = np.nonzero(boundary & active)
    bx_m = (bx / max(scatter.shape[1] - 1, 1) - 0.5) * lateral_mm / 1000.0
    bz_m = (by / max(scatter.shape[0] - 1, 1)) * depth_mm / 1000.0
    # Contrast is proportional to impedance discontinuity represented by boundary.
    boundary_amp = (2.5 + rng.normal(0, 0.3, len(by))).astype(np.float32)
    positions = np.column_stack([np.r_[x, bx_m], np.r_[z, bz_m]]).astype(np.float32)
    amplitudes = np.r_[diffuse, boundary_amp].astype(np.float32)
    if len(amplitudes) > max_scatterers:
        pick = rng.choice(len(amplitudes), max_scatterers, replace=False)
        positions, amplitudes = positions[pick], amplitudes[pick]
    return positions, amplitudes
