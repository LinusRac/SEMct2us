from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class Tissue:
    speed: float
    density: float
    attenuation: float
    scatter: float


TISSUES = {
    "air": Tissue(343.0, 1.2, 1.0, 0.0),
    "fat": Tissue(1450.0, 920.0, 0.6, 0.55),
    "soft": Tissue(1540.0, 1050.0, 0.5, 1.0),
    "bone": Tissue(3500.0, 1900.0, 12.0, 0.2),
    "fluid": Tissue(1480.0, 1000.0, 0.02, 0.08),
}


def make_acoustic_map(hu: np.ndarray, labels: np.ndarray) -> dict[str, np.ndarray]:
    """Map CT HU and labels to speed, density, attenuation, impedance, and scattering.

    Labels ensure anatomical voxels are modeled as tissue even where contrast or
    partial-volume HU values would otherwise be ambiguous. Label boundaries are
    explicitly retained for specular reflector generation.
    """
    kind = np.full(hu.shape, "soft", dtype="U8")
    kind[hu < -700] = "air"
    kind[(hu >= -700) & (hu < -30)] = "fat"
    kind[hu > 300] = "bone"
    # TotalSegmentator labels are anatomy masks. They override non-air CT voxels
    # to soft tissue and preserve every organ interface as a reflector.
    kind[(labels > 0) & (hu >= -700) & (hu <= 300)] = "soft"
    speed = np.zeros_like(hu, dtype=np.float32)
    density = np.zeros_like(hu, dtype=np.float32)
    attenuation = np.zeros_like(hu, dtype=np.float32)
    scatter = np.zeros_like(hu, dtype=np.float32)
    for name, tissue in TISSUES.items():
        mask = kind == name
        speed[mask], density[mask] = tissue.speed, tissue.density
        attenuation[mask], scatter[mask] = tissue.attenuation, tissue.scatter
    impedance = speed * density
    boundary = np.zeros_like(labels, dtype=bool)
    for axis in range(labels.ndim):
        current = [slice(None)] * labels.ndim
        previous = [slice(None)] * labels.ndim
        current[axis] = slice(1, None)
        previous[axis] = slice(None, -1)
        boundary[tuple(current)] |= labels[tuple(current)] != labels[tuple(previous)]
    gradients = np.gradient(hu.astype(np.float32))
    hu_boundary = np.sqrt(sum(gradient ** 2 for gradient in gradients)) > 80
    boundary |= hu_boundary
    return {"speed_m_s": speed, "density_kg_m3": density, "attenuation_db_cm_mhz": attenuation,
            "impedance_rayl": impedance, "diffuse_scatter": scatter, "boundary": boundary.astype(np.uint8),
            "labels": labels.astype(np.int16)}
